"""
ui/config_panel.py – Left sidebar configuration editor for F1LapForge Alpha 4.0
Renders all editable parameters with number inputs + bounds.
Uses global unique key generator to prevent StreamlitDuplicateElementKey.
"""

import streamlit as st
from typing import Dict, Any
from utils.validation import validate_config

def render_config_panel(config: Dict[str, Any]):
    """
    Renders the full configuration editor in the left column.
    All widget keys are made globally unique using a session counter.
    """
    st.caption("All changes are applied immediately when Live Preview is enabled")

    # Get current constructor and strategy
    constructor_name = config["runtime"].get("default_constructor", "generic")
    current_strategy = config["runtime"].get("default_strategy", "aggressive")

    if constructor_name not in config.get("constructors", {}):
        st.error(f"Constructor '{constructor_name}' not found")
        return

    constructor_cfg = config["constructors"][constructor_name]

    # Helper to get a guaranteed unique key for every widget
    def unique_key(base_name: str) -> str:
        if "widget_counter" not in st.session_state:
            st.session_state.widget_counter = 0
        st.session_state.widget_counter += 1
        return f"{base_name}_{st.session_state.widget_counter}"

    # ── Runtime Settings ────────────────────────────────────────────────────────
    with st.expander("Runtime Settings", expanded=True):
        config["runtime"]["tyre_compound"] = st.selectbox(
            "Tyre Compound",
            options=["soft", "medium"],
            index=0 if config["runtime"].get("tyre_compound") == "soft" else 1,
            key=unique_key("tyre_compound")
        )
        config["runtime"]["realism_multiplier"] = st.number_input(
            "Realism Multiplier",
            min_value=0.8, max_value=1.2, step=0.001, format="%.3f",
            value=float(config["runtime"].get("realism_multiplier", 0.965)),
            key=unique_key("realism_multiplier")
        )

    # ── Environment ─────────────────────────────────────────────────────────────
    with st.expander("Environment", expanded=False):
        race_key = config["runtime"].get("default_race_key", "china")
        env = config["environment"].get(race_key, config["environment"]["default"])
        env["air_temp_c"] = st.number_input(
            "Air Temperature (°C)",
            min_value=-10.0, max_value=60.0, step=0.5,
            value=float(env.get("air_temp_c", 20.0)),
            key=unique_key("air_temp_c")
        )
        env["track_temp_c"] = st.number_input(
            "Track Temperature (°C)",
            min_value=0.0, max_value=80.0, step=0.5,
            value=float(env.get("track_temp_c", 35.0)),
            key=unique_key("track_temp_c")
        )
        env["wind_speed_kmh"] = st.number_input(
            "Wind Speed (km/h)",
            min_value=0.0, max_value=50.0, step=1.0,
            value=float(env.get("wind_speed_kmh", 10.0)),
            key=unique_key("wind_speed_kmh")
        )

    # ── Powertrain ──────────────────────────────────────────────────────────────
    with st.expander("Powertrain", expanded=False):
        pt = constructor_cfg.get("powertrain", {})
        pt["ice_power_kw"] = st.number_input(
            "ICE Power (kW)",
            min_value=300.0, max_value=500.0, step=1.0,
            value=float(pt.get("ice_power_kw", 400.0)),
            key=unique_key("ice_power_kw")
        )
        pt["total_pu_kw"] = st.number_input(
            "Total PU Power (kW)",
            min_value=600.0, max_value=800.0, step=1.0,
            value=float(pt.get("total_pu_kw", 750.0)),
            key=unique_key("total_pu_kw")
        )

    # ── ERS ─────────────────────────────────────────────────────────────────────
    with st.expander("ERS Settings", expanded=False):
        ers = constructor_cfg.get("ers", {})
        ers["deploy_efficiency"] = st.number_input(
            "Deploy Efficiency",
            min_value=0.70, max_value=0.99, step=0.01,
            value=float(ers.get("deploy_efficiency", 0.92)),
            key=unique_key("deploy_efficiency")
        )
        ers["harvest_efficiency"] = st.number_input(
            "Harvest Efficiency",
            min_value=0.70, max_value=0.99, step=0.01,
            value=float(ers.get("harvest_efficiency", 0.85)),
            key=unique_key("harvest_efficiency")
        )
        ers["thermal_duty_threshold"] = st.number_input(
            "Thermal Duty Threshold",
            min_value=0.50, max_value=0.90, step=0.01,
            value=float(ers.get("thermal_duty_threshold", 0.72)),
            key=unique_key("thermal_duty_threshold")
        )
        ers["max_harvest_mj_per_lap_quali"] = st.number_input(
            "Max Harvest per Lap Quali (MJ)",
            min_value=5.0, max_value=9.0, step=0.1,
            value=float(ers.get("max_harvest_mj_per_lap_quali", 7.0)),
            key=unique_key("max_harvest_mj")
        )

    # ── Chassis ─────────────────────────────────────────────────────────────────
    with st.expander("Chassis", expanded=False):
        chassis = constructor_cfg.get("chassis", {})
        chassis["cd_straight_base"] = st.number_input(
            "Cd Straight Base",
            min_value=0.6, max_value=1.0, step=0.01,
            value=float(chassis.get("cd_straight_base", 0.78)),
            key=unique_key("cd_straight_base")
        )
        chassis["cla_corner"] = st.number_input(
            "Cla Corner",
            min_value=-5.0, max_value=-3.0, step=0.01,
            value=float(chassis.get("cla_corner", -4.1)),
            key=unique_key("cla_corner")
        )

    # ── Tyres ───────────────────────────────────────────────────────────────────
    with st.expander("Tyres", expanded=False):
        tyres = constructor_cfg.get("tyres", {})
        for compound in ["soft", "medium"]:
            if compound in tyres:
                compound_cfg = tyres[compound]
                compound_cfg["grip_multiplier"] = st.number_input(
                    f"{compound.capitalize()} Grip Multiplier",
                    min_value=0.8, max_value=1.2, step=0.01,
                    value=float(compound_cfg.get("grip_multiplier", 1.05)),
                    key=unique_key(f"{compound}_grip")
                )

    # ── Driver Style ────────────────────────────────────────────────────────────
    with st.expander("Driver Style", expanded=False):
        driver = constructor_cfg.get("driver_style", {})
        driver["trail_brake_factor"] = st.number_input(
            "Trail Brake Factor",
            min_value=0.8, max_value=1.3, step=0.01,
            value=float(driver.get("trail_brake_factor", 1.0)),
            key=unique_key("trail_brake_factor")
        )

    # ── Strategy Settings ───────────────────────────────────────────────────────
    with st.expander("Strategy Settings", expanded=False):
        if current_strategy == "auto_optimizer":
            st.info("Auto-optimizer is active — strategy parameters are optimized automatically. Manual editing disabled.")
        else:
            if current_strategy not in config.get("strategies", {}):
                st.error(f"Strategy '{current_strategy}' not found in config")
            else:
                strat = config["strategies"][current_strategy]
                strat["deploy_factor_base"] = st.number_input(
                    "Deploy Factor Base",
                    min_value=0.5, max_value=1.5, step=0.01,
                    value=float(strat.get("deploy_factor_base", 1.08)),
                    key=unique_key("deploy_factor_base")
                )
                strat["harvest_factor_base"] = st.number_input(
                    "Harvest Factor Base",
                    min_value=0.5, max_value=1.5, step=0.01,
                    value=float(strat.get("harvest_factor_base", 1.10)),
                    key=unique_key("harvest_factor_base")
                )
                strat["target_final_soc_mj"] = st.number_input(
                    "Target Final SOC (MJ)",
                    min_value=0.0, max_value=4.0, step=0.1,
                    value=float(strat.get("target_final_soc_mj", 0.60)),
                    key=unique_key("target_final_soc_mj")
                )
                strat["thermal_duty_threshold"] = st.number_input(
                    "Thermal Duty Threshold",
                    min_value=0.5, max_value=0.9, step=0.01,
                    value=float(strat.get("thermal_duty_threshold", 0.72)),
                    key=unique_key("thermal_duty_threshold")
                )

    # ── Validate Config button ──────────────────────────────────────────────────
    if st.button("Validate Config"):
        try:
            validate_config(config)
            st.success("Configuration is valid!")
        except ValueError as e:
            st.error(str(e))