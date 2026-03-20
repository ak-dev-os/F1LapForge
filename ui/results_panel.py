"""
ui/results_panel.py – Results display component for F1LapForge Alpha 4.0
Developed by Karthik

Shows:
- Summary metrics (lap time, final SOC, harvest)
- Segment breakdown table
- Consolidated multi-y-axis chart (used in Results & Analysis tab)
- Four individual charts (used in Visualisation tab)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.format import format_lap_time_hms


def render_results_panel(results_dict: dict, tab_mode: str = "results"):
    """
    Main rendering function for results.
    
    Args:
        results_dict: dict with keys 'results', 'lap_time', 'final_soc', 'harvest'
        tab_mode: "results" → consolidated chart + table
                  "visuals" → four individual charts
    """
    if not results_dict or "results" not in results_dict:
        st.info("No simulation results available yet.")
        return

    df = pd.DataFrame(results_dict["results"])

    # ── Summary metrics (shown in both tabs) ────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    col1.metric("Lap Time", format_lap_time_hms(results_dict["lap_time"]))
    col2.metric("Final SOC", f"{results_dict['final_soc']:.2f} MJ")
    col3.metric("Energy Harvest", f"{results_dict['harvest']:.1f} MJ")

    # ── Segment breakdown table (shown in Results tab only) ─────────────────────
    if tab_mode == "results":
        st.subheader("Segment Breakdown")
        st.dataframe(
            df[["segment", "time_s", "speed_kmh", "throttle_pct", "brake_pct", "soc_mj", "mgu_kw", "harvest_kw"]]
            .style.format({
                "time_s": lambda x: format_lap_time_hms(x),
                "speed_kmh": "{:.1f} km/h",
                "throttle_pct": "{:.1f}%",
                "brake_pct": "{:.1f}%",
                "soc_mj": "{:.2f} MJ",
                "mgu_kw": "{:.0f} kW",
                "harvest_kw": "{:.0f} kW"
            })
            .background_gradient(subset=["soc_mj"], cmap="RdYlGn_r", low=0.4, high=0.8)
        )

    # ── Chart logic ─────────────────────────────────────────────────────────────
    if "cum_dist_km" not in df.columns:
        df["cum_dist_km"] = df.index * 0.1  # fallback if no distance column

    # Colors used consistently
    colors = {
        "speed": "#FF7043",
        "deploy": "#1976D2",
        "harvest": "#00897B",
        "soc": "#D32F2F",
        "throttle": "#4CAF50",
        "brake": "#F44336"
    }

    # ── Consolidated chart (Results & Analysis tab) ─────────────────────────────
    if tab_mode == "results":
        st.subheader("Consolidated Lap Telemetry")
        fig_cons = make_subplots(specs=[[{"secondary_y": True}]])

        # Speed (primary y-axis)
        fig_cons.add_trace(
            go.Scatter(x=df["cum_dist_km"], y=df["speed_kmh"],
                       name="Speed (km/h)", line=dict(color=colors["speed"], width=3)),
            secondary_y=False
        )

        # Deploy & Harvest (secondary y-axis)
        fig_cons.add_trace(
            go.Scatter(x=df["cum_dist_km"], y=df["mgu_kw"],
                       name="Deploy (kW)", line=dict(color=colors["deploy"])),
            secondary_y=True
        )
        fig_cons.add_trace(
            go.Scatter(x=df["cum_dist_km"], y=df["harvest_kw"],
                       name="Harvest (kW)", line=dict(color=colors["harvest"], dash="dash")),
            secondary_y=True
        )

        # SOC (secondary y-axis – right side)
        fig_cons.add_trace(
            go.Scatter(x=df["cum_dist_km"], y=df["soc_mj"],
                       name="SOC (MJ)", line=dict(color=colors["soc"])),
            secondary_y=True
        )

        fig_cons.update_layout(
            title="Lap Telemetry – All Key Parameters",
            xaxis_title="Distance (km)",
            yaxis_title="Speed (km/h)",
            yaxis2_title="Power (kW) / SOC (MJ)",
            height=650,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
            template="plotly_white"
        )

        st.plotly_chart(fig_cons, use_container_width=True)

    # ── Individual charts (Visualisation tab) ───────────────────────────────────
    elif tab_mode == "visuals":
        st.subheader("Individual Telemetry Charts")

        # Chart 1: Speed Profile
        fig_speed = go.Figure()
        fig_speed.add_trace(go.Scatter(
            x=df["cum_dist_km"], y=df["speed_kmh"],
            name="Speed", line=dict(color=colors["speed"], width=3)
        ))
        fig_speed.update_layout(title="Speed Profile", xaxis_title="Distance (km)", yaxis_title="Speed (km/h)", height=400)
        st.plotly_chart(fig_speed, use_container_width=True)

        # Chart 2: Deploy & Harvest Power
        fig_power = go.Figure()
        fig_power.add_trace(go.Scatter(x=df["cum_dist_km"], y=df["mgu_kw"], name="Deploy", line=dict(color=colors["deploy"])))
        fig_power.add_trace(go.Scatter(x=df["cum_dist_km"], y=df["harvest_kw"], name="Harvest", line=dict(color=colors["harvest"], dash="dash")))
        fig_power.update_layout(title="MGU-K Deploy & Harvest Power", xaxis_title="Distance (km)", yaxis_title="Power (kW)", height=400)
        st.plotly_chart(fig_power, use_container_width=True)

        # Chart 3: Battery SOC
        fig_soc = go.Figure()
        fig_soc.add_trace(go.Scatter(x=df["cum_dist_km"], y=df["soc_mj"], name="SOC", line=dict(color=colors["soc"])))
        fig_soc.update_layout(title="Battery SOC", xaxis_title="Distance (km)", yaxis_title="SOC (MJ)", height=400)
        st.plotly_chart(fig_soc, use_container_width=True)

        # Chart 4: Throttle & Brake
        fig_pedal = go.Figure()
        fig_pedal.add_trace(go.Scatter(x=df["cum_dist_km"], y=df["throttle_pct"], name="Throttle", line=dict(color=colors["throttle"])))
        fig_pedal.add_trace(go.Scatter(x=df["cum_dist_km"], y=df["brake_pct"], name="Brake", line=dict(color=colors["brake"])))
        fig_pedal.update_layout(title="Throttle & Brake Pedal", xaxis_title="Distance (km)", yaxis_title="Pedal (%)", height=400)
        st.plotly_chart(fig_pedal, use_container_width=True)