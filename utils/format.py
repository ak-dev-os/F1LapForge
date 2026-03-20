"""
utils/format.py – Formatting utilities for F1LapForge
Contains helper functions for displaying lap times and other values.
"""

def format_lap_time_hms(seconds: float) -> str:
    """
    Convert lap time in seconds to classic F1 format: M:SS.mmm
    
    Examples:
        78.518  → "1:18.518"
        91.520  → "1:31.520"
        3599.999 → "59:59.999"
    
    Args:
        seconds: Time in decimal seconds
        
    Returns:
        Formatted string
    """
    if seconds < 0:
        return "--:--.---"
        
    minutes = int(seconds // 60)
    remaining = seconds - (minutes * 60)
    return f"{minutes}:{remaining:06.3f}"


def format_delta_time(seconds: float, include_sign: bool = True) -> str:
    """
    Format a time delta (positive or negative) with sign.
    
    Examples:
        0.312   → "+0.312"
        -0.085  → "-0.085"
        0.000   → "0.000"
    """
    if abs(seconds) < 0.001:
        return "0.000"
    
    sign = "+" if seconds >= 0 and include_sign else ""
    return f"{sign}{seconds:+.3f}" if include_sign else f"{seconds:.3f}"