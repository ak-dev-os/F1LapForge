"""
ui/presets.py – Preset save/load logic for Alpha 4.0
Handles download and upload of custom YAML configurations.
"""

import streamlit as st
from utils.yaml import save_yaml, load_yaml
from datetime import datetime

def save_preset(config: dict, name: str = "custom"):
    """
    Generate downloadable YAML preset.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.yaml"
    
    yaml_str = save_yaml(config, filename)  # returns nothing, saves to file
    with open(filename, "r", encoding="utf-8") as f:
        yaml_content = f.read()
    
    st.download_button(
        label="Download Preset",
        data=yaml_content,
        file_name=filename,
        mime="text/yaml"
    )

def load_preset(uploaded_file):
    """
    Load user-uploaded YAML preset.
    Returns parsed dict or None if invalid.
    """
    if uploaded_file is not None:
        try:
            config = load_yaml(uploaded_file)
            st.success(f"Loaded: {uploaded_file.name}")
            return config
        except Exception as e:
            st.error(f"Failed to load preset: {str(e)}")
            return None
    return None