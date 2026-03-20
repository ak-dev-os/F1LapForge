"""
app.py – F1LapForge Alpha 4.0 – Main Streamlit application
Developed by Karthik

Full configuration moved to left sidebar.
Main area uses three tabs:
- Results & Analysis (metrics + table + consolidated chart)
- Visualisation (individual charts)
- Debug Logs (log file viewer)
"""

import streamlit as st
import pandas as pd
import time
from pathlib import Path
import logging

from utils.yaml import load_yaml, save_yaml, merge_configs
from utils.validation import validate_config
from ui.config_panel import render_config_panel
from ui.results_panel import render_results_panel
from ui.presets import save_preset, load_preset
from model.core import simulate_lap
from model.optimization import run_auto_optimization

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simulation_log.txt", mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ── Session state initialization ──────────────────────────────────────────────
if "current_config" not in st.session_state:
    st.session_state.current_config = load_yaml("config_runtime.yaml")
if "last_results" not in st.session_state:
    st.session_state.last_results = None
if "live_preview" not in st.session_state:
    st.session_state.live_preview = False
if "simulation_running" not in st.session_state:
    st.session_state.simulation_running = False
if "last_run_time" not in st.session_state:
    st.session_state.last_run_time = 0

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(page_title="F1LapForge Alpha 4.0", layout="wide")

st.title("F1LapForge – Alpha 4.0")
st.caption("Interactive 2026 F1 Engineering & Strategy Analysis Tool")

# ── Left Sidebar: Full Configuration ──────────────────────────────────────────
with st.sidebar:
    st.header("Configuration")

    # Race selector
    race_options = list(load_yaml("tracks_2026.yaml")["races"].keys())
    selected_race = st.selectbox(
        "Select Race",
        options=race_options,
        index=race_options.index(st.session_state.current_config["runtime"]["default_race_key"])
        if st.session_state.current_config["runtime"]["default_race_key"] in race_options else 0,
        key="race_selector"
    )
    if selected_race != st.session_state.current_config["runtime"]["default_race_key"]:
        st.session_state.current_config["runtime"]["default_race_key"] = selected_race
        st.rerun()

    # Constructor selector
    constructor_options = list(st.session_state.current_config["constructors"].keys())
    selected_constructor = st.selectbox(
        "Select Constructor",
        options=constructor_options,
        index=constructor_options.index(st.session_state.current_config["runtime"]["default_constructor"])
        if st.session_state.current_config["runtime"]["default_constructor"] in constructor_options else 0,
        key="constructor_selector"
    )
    if selected_constructor != st.session_state.current_config["runtime"]["default_constructor"]:
        st.session_state.current_config["runtime"]["default_constructor"] = selected_constructor
        st.rerun()

    # Strategy selector
    strategy_options = list(st.session_state.current_config["strategies"].keys())
    selected_strategy = st.selectbox(
        "Select Strategy",
        options=strategy_options,
        index=strategy_options.index(st.session_state.current_config["runtime"]["default_strategy"])
        if st.session_state.current_config["runtime"]["default_strategy"] in strategy_options else 0,
        key="strategy_selector"
    )
    if selected_strategy != st.session_state.current_config["runtime"]["default_strategy"]:
        st.session_state.current_config["runtime"]["default_strategy"] = selected_strategy
        st.rerun()

    # All other configuration fields
    render_config_panel(st.session_state.current_config)

    # Presets section
    st.markdown("---")
    st.subheader("Presets")
    preset_name = st.text_input("Preset name", "custom_strategy", key="preset_name_input")
    col_save, col_load = st.columns(2)
    with col_save:
        if st.button("Save Preset"):
            save_preset(st.session_state.current_config, preset_name)
            st.success("Saved!")
    with col_load:
        uploaded = st.file_uploader("Load Preset", type=["yaml", "yml"], key="load_preset_uploader")
        if uploaded:
            loaded = load_preset(uploaded)
            if loaded:
                st.session_state.current_config = loaded
                st.success("Loaded!")
                st.rerun()

# ── Main area: Tabs ────────────────────────────────────────────────────────────
tab_results, tab_visuals, tab_logs = st.tabs(["Results & Analysis", "Visualisation", "Debug Logs"])

with tab_results:
    st.subheader("Results & Analysis")

    live_preview = st.checkbox("Live Preview (re-run on change)", value=st.session_state.live_preview)
    st.session_state.live_preview = live_preview

    if st.button("Run Simulation", type="primary", disabled=st.session_state.simulation_running):
        st.session_state.simulation_running = True
        with st.spinner("Running simulation..."):
            try:
                validate_config(st.session_state.current_config)
                race_key = st.session_state.current_config["runtime"]["default_race_key"]
                race_cfg = load_yaml("tracks_2026.yaml")["races"][race_key]
                env_cfg = st.session_state.current_config["environment"][race_key]
                strategy_name = st.session_state.current_config["runtime"]["default_strategy"]
                constructor_name = st.session_state.current_config["runtime"]["default_constructor"]

                base_cfg = st.session_state.current_config["constructors"]["generic"]
                override_cfg = st.session_state.current_config["constructors"].get(constructor_name, {})
                merged_cfg = merge_configs(base_cfg, override_cfg)

                if strategy_name == "auto_optimizer":
                    results, lap_time, final_soc, harvest = run_auto_optimization(
                        merged_cfg, race_cfg, st.session_state.current_config, env_cfg, None
                    )
                else:
                    results, lap_time, final_soc, harvest = simulate_lap(
                        merged_cfg, race_cfg, strategy_name, env_cfg, st.session_state.current_config, None
                    )

                st.session_state.last_results = {
                    "results": results,
                    "lap_time": lap_time,
                    "final_soc": final_soc,
                    "harvest": harvest
                }
                st.success(f"Simulation completed! Lap time: {lap_time:.3f}s | Final SOC: {final_soc} MJ")

            except Exception as e:
                st.error(f"Simulation failed: {type(e).__name__} – {str(e)}")
                st.session_state.last_results = None

        st.session_state.simulation_running = False
        st.rerun()

    if st.session_state.last_results:
        render_results_panel(st.session_state.last_results, tab_mode="results")
    else:
        st.info("Press 'Run Simulation' to see results")

with tab_visuals:
    st.subheader("Visualisation")
    if st.session_state.last_results:
        render_results_panel(st.session_state.last_results, tab_mode="visuals")
    else:
        st.info("Run a simulation to see detailed charts")

with tab_logs:
    st.subheader("Debug Logs")
    try:
        with open("simulation_log.txt", "r") as f:
            logs = f.read()
        st.text_area("simulation_log.txt content", logs, height=500)
    except FileNotFoundError:
        st.info("simulation_log.txt not found yet — run a simulation first")
    if st.button("Refresh Logs"):
        st.rerun()