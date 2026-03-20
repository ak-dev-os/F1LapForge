"""
model/optimization.py – Auto-optimization logic for F1LapForge
Uses scipy to find best deploy/harvest factors.
"""

from scipy.optimize import minimize
import numpy as np
from model.core import simulate_lap
from strategies import get_strategy_params

def run_auto_optimization(merged_cfg, race_cfg, runtime_cfg, env_cfg, pole_ref=None):
    """
    Gradient-based optimization for auto_optimizer strategy.
    Returns results of the best lap found.
    """
    def objective(x):
        df, hf = x
        df = np.clip(df, *runtime_cfg["strategies"]["auto_optimizer"]["deploy_factor_bounds"])
        hf = np.clip(hf, *runtime_cfg["strategies"]["auto_optimizer"]["harvest_factor_bounds"])

        temp_strategy = runtime_cfg["strategies"]["aggressive"].copy()
        temp_strategy["deploy_factor_base"] = float(df)
        temp_strategy["harvest_factor_base"] = float(hf)

        _, lap_time, final_soc, _ = simulate_lap(
            merged_cfg, race_cfg, "aggressive", env_cfg, runtime_cfg, pole_ref,
            override_strategy=temp_strategy
        )
        penalty = 0
        if final_soc < temp_strategy["soc_floor_penalty_threshold"]:
            penalty += 12 * (temp_strategy["soc_floor_penalty_threshold"] - final_soc) ** 2
        return lap_time + penalty

    initial = [
        runtime_cfg["strategies"]["aggressive"]["deploy_factor_base"],
        runtime_cfg["strategies"]["aggressive"]["harvest_factor_base"]
    ]
    bounds = [
        runtime_cfg["strategies"]["auto_optimizer"]["deploy_factor_bounds"],
        runtime_cfg["strategies"]["auto_optimizer"]["harvest_factor_bounds"]
    ]

    result = minimize(objective, initial, bounds=bounds, method='L-BFGS-B', tol=1e-5)
    df_opt, hf_opt = result.x

    opt_strategy = runtime_cfg["strategies"]["aggressive"].copy()
    opt_strategy["deploy_factor_base"] = float(df_opt)
    opt_strategy["harvest_factor_base"] = float(hf_opt)

    return simulate_lap(
        merged_cfg, race_cfg, "aggressive", env_cfg, runtime_cfg, pole_ref,
        override_strategy=opt_strategy
    )