"""
utils/yaml.py – YAML file handling utilities for F1LapForge
Provides safe loading, saving, and merging of configuration dictionaries.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def load_yaml(filepath: str | Path) -> Dict[str, Any]:
    """
    Safely load a YAML file into a Python dictionary.
    
    Args:
        filepath: Path to the YAML file (str or Path object)
        
    Returns:
        Dict containing the parsed YAML content
        
    Raises:
        FileNotFoundError: If the file does not exist
        yaml.YAMLError: If the YAML is malformed
        ValueError: For other parsing issues
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")
    
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(f"YAML root must be a dictionary, got {type(data).__name__}")
        logger.debug(f"Loaded YAML from {path} with {len(data)} top-level keys")
        return data
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML format in {path}: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error loading YAML {path}: {str(e)}") from e


def save_yaml(data: Dict[str, Any], filepath: str | Path, sort_keys: bool = False) -> None:
    """
    Save a dictionary to a YAML file with clean formatting.
    
    Args:
        data: Dictionary to save
        filepath: Destination path
        sort_keys: Whether to sort dictionary keys (default: False)
        
    Raises:
        IOError: If writing to file fails
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                data,
                f,
                sort_keys=sort_keys,
                allow_unicode=True,
                default_flow_style=False,
                indent=2
            )
        logger.info(f"Saved YAML to {path}")
    except Exception as e:
        raise IOError(f"Failed to save YAML to {path}: {str(e)}") from e


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge override dictionary into base dictionary.
    Used to apply constructor-specific overrides on top of generic defaults.
    
    - Simple values in override overwrite base
    - Dictionaries are merged recursively
    
    Returns a new merged dictionary (does not modify inputs)
    
    Logs warning if critical sections are missing after merge.
    """
    merged = base.copy()
    
    for key, value in override.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    
    # Safety check: warn if important sections are missing
    critical_sections = ["ers", "powertrain", "chassis", "tyres"]
    missing = [s for s in critical_sections if s not in merged]
    if missing:
        logger.warning(f"After merge, missing critical sections: {missing}")
    
    logger.debug(f"Merged config has {len(merged)} top-level keys: {list(merged.keys())}")
    return merged