"""
model/core.py – Core physics engine for F1LapForge (Alpha 4.0)
All first-principles calculations.
Pure functional style. No classes.
"""

import math
import logging

# Logging setup for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("simulation_log.txt", mode='a'),
            logging.StreamHandler()
        ]
    )

from strategies import get_strategy_params

def apply_speed_derate(v_kmh: float, base_power: float, derate_start: float, derate_full: float) -> float:
    logger.debug(f"Applying speed derate at {v_kmh:.1f} km/h")
    if v_kmh <= derate_start:
        return base_power
    if v_kmh >= derate_full:
        return 0.0
    frac = (v_kmh - derate_start) / (derate_full - derate_start)
    return base_power * (1 - frac)

def segment_dynamics(seg: dict, throttle_pct: float, rpm_pct: float, brake_pct: float,
                     soc_mj: float, lap_time_so_far: float, cum_deploy_mj: float,
                     cfg: dict, env: dict, strategy: dict, runtime_cfg: dict,
                     prev_speed_kmh: float = 180.0):
    """
    Calculates physics for one track segment using Euler integration (10 ms steps).
    """
    length_m = seg["length_m"]
    corner_r = seg.get("corner_radius_m", 0)
    is_straight = seg["type"] == "STRAIGHT"

    # Tyre grip adjustment (temperature + warm-up)
    optimal_track = 40.0
    temp_dev = abs(env["track_temp_c"] - optimal_track) / 10.0
    grip_temp_factor = max(0.88, 1.0 - 0.05 * temp_dev)   # 5% drop per 10°C deviation

    warm_up_adjust = max(0.92, 1.0 - 0.003 * (35.0 - env["track_temp_c"]) * (20.0 - env["air_temp_c"]) / 10.0)

    compound = runtime_cfg["runtime"]["tyre_compound"]
    tyre_cfg = cfg["tyres"][compound]  # FIX: direct access (no 'compounds' subkey)
    grip = tyre_cfg["grip_multiplier"]
    grip *= grip_temp_factor * warm_up_adjust * min(
        1.0, lap_time_so_far / (15.0 * (35.0 / max(env["track_temp_c"], 10.0)))
    )

    # Drag
    cd = cfg["chassis"]["cd_straight_base"]
    if is_straight and throttle_pct > 80:
        cd *= (1 - cfg["chassis"]["drs_reduction"])
    wind_factor = 1.0 + (env["wind_speed_kmh"] / 100.0) * 0.015 if is_straight else 1.0
    cd *= wind_factor

    # Power
    deploy_kw = min(cfg["ers"]["P_K_max_kW"] * strategy["deploy_factor_base"] * (throttle_pct / 100),
                    soc_mj * 1000)
    deploy_kw = min(deploy_kw, prev_speed_kmh * strategy["deploy_ramp_rate_kws"] / 100)
    deploy_kw = apply_speed_derate(prev_speed_kmh, deploy_kw,
                                   strategy["speed_derate_start_kmh"],
                                   strategy["speed_derate_full_kmh"])

    power_kw = cfg["powertrain"]["ice_power_kw"] * (throttle_pct / 100) * (rpm_pct / 100) + deploy_kw

    # Euler integration
    v_ms = prev_speed_kmh / 3.6
    time_s = 0.0
    dist = 0.0
    seg_deploy_mj = 0.0
    seg_harvest_mj = 0.0

    while dist < length_m:
        dt = 0.01
        drag = 0.5 * 1.225 * cd * cfg["chassis"]["reference_area_m2"] * v_ms**2
        rolling = 0.015 * cfg["chassis"]["mass_kg"] * 9.81
        net_force = (power_kw * 1000 / max(v_ms, 5)) - drag - rolling
        accel = net_force / cfg["chassis"]["mass_kg"]

        if corner_r > 0:
            mu_lat = tyre_cfg.get("mu_lat", 2.0)
            v_max_ms = math.sqrt(mu_lat * 9.81 * corner_r * 1.05)
            if v_ms > v_max_ms:
                accel = min(accel, -2.5)

        v_ms += accel * dt
        v_ms = max(5.0, v_ms)
        dist += v_ms * dt
        time_s += dt

        seg_deploy_mj += deploy_kw * dt / 1000
        if brake_pct > 20 or seg["type"] in ["CORNER", "MIXED"]:
            harvest_kw = min(strategy["super_clip_harvest_kw_cap"],
                             brake_pct/100 * 350 * strategy["harvest_factor_base"] * cfg["ers"]["harvest_efficiency"])
            seg_harvest_mj += harvest_kw * dt / 1000

    exit_speed = min(332, v_ms * 3.6 * 0.98)

    # Thermal fade
    if cum_deploy_mj > strategy["thermal_duty_threshold"] * 4.0:
        fade = 1 - 0.25 * (cum_deploy_mj - strategy["thermal_duty_threshold"] * 4.0) / (4.0 - strategy["thermal_duty_threshold"] * 4.0)
        power_kw *= max(0.6, fade)

    soc_new = min(4.0, max(0.1, soc_mj - seg_deploy_mj / cfg["ers"]["deploy_efficiency"] + seg_harvest_mj))

    penalty = 0.0
    if soc_new < strategy["soc_floor_penalty_threshold"]:
        penalty = 10 * (strategy["soc_floor_penalty_threshold"] - soc_new) ** 2

    time_s = max(time_s, seg["baseline_time_s"] * 0.96) * runtime_cfg["runtime"]["realism_multiplier"]

    logger.debug(f"Segment {seg['name']} completed: time={time_s:.3f}s, exit_speed={exit_speed:.1f} km/h")
    return {
        "time_s": time_s + penalty,
        "speed_kmh": round(exit_speed, 1),
        "soc_mj": round(soc_new, 2),
        "throttle_pct": throttle_pct,
        "brake_pct": brake_pct,
        "mgu_kw": round(deploy_kw),
        "harvest_kw": round(min(strategy["super_clip_harvest_kw_cap"], seg_harvest_mj * 1000 / time_s if time_s > 0 else 0)),
        "penalty_s": penalty,
        "deploy_mj": seg_deploy_mj,
        "harvest_mj": seg_harvest_mj
    }

def simulate_lap(merged_cfg: dict, race_cfg: dict, strategy_name: str, env_cfg: dict, runtime_cfg: dict, pole_ref: float = None, override_strategy: dict = None):
    logger.info("simulate_lap started")
    if override_strategy is not None:
        strategy = override_strategy
    else:
        strategy = get_strategy_params(strategy_name, runtime_cfg["strategies"])

    # ERS is directly under merged_cfg (constructor level)
    if "ers" not in merged_cfg:
        logger.error("No 'ers' section in merged_cfg - check merge_configs usage")
        raise KeyError("No 'ers' section in merged constructor config")
    ers = merged_cfg["ers"]

    segments = race_cfg["segments"]
    results = []
    soc = ers["SOC_max_MJ"] * 0.95
    lap_time = 0.0
    prev_speed = 180.0
    cum_deploy = 0.0
    total_harvest = 0.0

    base_strategy_map = {
        "STRAIGHT": (98, 1.0, 0),
        "CORNER": (64, 0.82, 78),
        "MIXED": (85, 0.91, 22)
    }

    strategy_map = {k: (t[0] * strategy["deploy_factor_base"],
                        t[1],
                        t[2] * strategy["harvest_factor_base"]) for k, t in base_strategy_map.items()}

    for seg in segments:
        typ = seg["type"]
        throttle, rpm, brake = strategy_map.get(typ, (85, 0.91, 22))
        dyn = segment_dynamics(
            seg, throttle, rpm, brake, soc, lap_time, cum_deploy,
            merged_cfg, env_cfg, strategy, runtime_cfg, prev_speed
        )

        soc = dyn["soc_mj"]
        lap_time += dyn["time_s"]
        prev_speed = dyn["speed_kmh"]
        cum_deploy += dyn["deploy_mj"]
        total_harvest += dyn["harvest_mj"]

        dyn.update({"segment": seg["name"], "type": typ})
        results.append(dyn)

    if total_harvest > strategy["max_harvest_mj_per_lap_quali"]:
        scale = strategy["max_harvest_mj_per_lap_quali"] / total_harvest
        total_harvest *= scale
        for r in results:
            r["harvest_kw"] *= scale

    if strategy_name == "aggressive" and pole_ref is not None:
        scale_factor = pole_ref / lap_time if lap_time > 0 else 1.0
        lap_time = pole_ref
        for r in results:
            r["time_s"] *= scale_factor

    logger.info(f"simulate_lap completed: lap_time={lap_time:.3f}s, final_soc={soc:.2f}")
    return results, round(lap_time, 3), round(soc, 2), round(total_harvest, 2)