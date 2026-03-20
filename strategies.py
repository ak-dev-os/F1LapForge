"""
strategies.py – Strategy parameter loader for F1LapForge
Provides a simple interface to retrieve strategy configs from YAML.
Used by model/core.py to avoid hard-coding strategy logic.
"""

from typing import Dict, Any

def get_strategy_params(strategy_name: str, strategies_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve the full parameter dictionary for a given strategy name.
    
    Args:
        strategy_name: Name of the strategy (e.g. 'aggressive', 'balanced')
        strategies_cfg: The strategies dictionary from runtime config
        
    Returns:
        Dict containing the strategy parameters
        
    Raises:
        ValueError: If the strategy name does not exist
    """
    if strategy_name not in strategies_cfg:
        raise ValueError(f"Strategy '{strategy_name}' not found in config")
    
    return strategies_cfg[strategy_name]