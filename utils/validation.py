"""
utils/validation.py – Configuration validation helpers for F1LapForge Alpha 4.0
Ensures user inputs are within safe/realistic bounds before simulation.
"""

from typing import Dict, Any

def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate the entire user-modified configuration dictionary.
    Checks all required fields, especially inside the current constructor.
    
    Raises ValueError with descriptive message if anything is invalid.
    """
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a dictionary")

    # 1. Runtime section
    if "runtime" not in config:
        raise ValueError("Missing required section: runtime")
    
    runtime = config["runtime"]
    if runtime.get("realism_multiplier", 0) <= 0:
        raise ValueError("realism_multiplier must be positive")

    # 2. Current constructor must exist
    constructor_name = runtime.get("default_constructor")
    if not constructor_name or constructor_name not in config.get("constructors", {}):
        raise ValueError(f"Invalid or missing constructor: {constructor_name}")

    constructor_cfg = config["constructors"][constructor_name]

    # 3. ERS section inside current constructor
    if "ers" not in constructor_cfg:
        raise ValueError(f"Missing required section 'ers' in constructor '{constructor_name}'")
    
    ers = constructor_cfg["ers"]
    if ers.get("SOC_max_MJ", 0) <= 0:
        raise ValueError("SOC_max_MJ must be positive (FIA 2026 = 4.0)")
    if ers.get("P_K_max_kW", 0) <= 0 or ers["P_K_max_kW"] > 350:
        raise ValueError("P_K_max_kW must be between 0 and 350 kW (FIA limit)")
    for eff in ["deploy_efficiency", "harvest_efficiency"]:
        if not 0 < ers.get(eff, 0) <= 1:
            raise ValueError(f"{eff} must be between 0 and 1")
    if not 0 < ers.get("thermal_duty_threshold", 0) <= 1:
        raise ValueError("thermal_duty_threshold must be between 0 and 1")
    if ers.get("max_harvest_mj_per_lap_quali", 0) <= 0:
        raise ValueError("max_harvest_mj_per_lap_quali must be positive")

    # 4. Optional: check environment (if present)
    race_key = runtime.get("default_race_key")
    if "environment" in config and race_key in config["environment"]:
        env = config["environment"][race_key]
        if env.get("air_temp_c", -100) < -50 or env["air_temp_c"] > 60:
            raise ValueError("air_temp_c outside realistic range (-50°C to 60°C)")
        if env.get("track_temp_c", -100) < 0 or env["track_temp_c"] > 80:
            raise ValueError("track_temp_c outside realistic range (0°C to 80°C)")

    # Add more checks here as needed (powertrain, chassis, tyres, etc.)
    # For now, this covers the most critical parts used in simulation

    # All good
    return