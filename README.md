# F1LapForge – Alpha 4.0

**Interactive 2026 F1 Engineering & Strategy Analysis Tool**

F1LapForge is an open‑source, physics‑based simulation workbench for exploring 2026 Formula 1 car performance — with a strong focus on energy recovery system (ERS) deployment & harvesting strategies, power unit output, aerodynamics, tyre behaviour, and driver style under realistic FIA regulations.

It’s built for race engineers, sim racers, strategy analysts, and F1 enthusiasts who want to understand **why** one setup is faster than another, not just see a lap time.

---

## Current Features (Alpha 4.0 – March 2026)

### Interactive configuration (left sidebar)

Everything important is editable directly in the UI:

- **Race / circuit selection**
  - Circuits and segment definitions come from `tracks_2026.yaml` (e.g., China, Australia).
- **Constructor selection**
  - Generic baseline plus team‑specific overrides (Mercedes, Ferrari, RedBullFord, etc.).
- **Strategy selection**
  - Driving / ERS styles (`aggressive`, `balanced`, `conservative`, and `auto_optimizer` if enabled in config).
- **Powertrain**
  - ICE power and total PU power (`ice_power_kw`, `total_pu_kw`).
- **ERS parameters**
  - Battery capacity (`SOC_max_MJ`), MGU‑K max power (`P_K_max_kW`), deploy & harvest efficiency, thermal duty threshold, per‑lap harvest limit, SOC floor penalty threshold.
- **Chassis**
  - Mass, drag coefficients, downforce coefficients, reference area, DRS reduction.
- **Tyres**
  - Compound‑specific grip multipliers (soft / medium) and optional friction coefficients.
- **Driver style**
  - Trail‑brake factor and related driving parameters.
- **Environment**
  - Air temperature, track temperature, wind speed per race.

Changes are made against a single backing YAML config (`config_runtime.yaml`), so you can always export / version your setups.

### Simulation control

- **Live Preview** toggle  
  When enabled, the app will automatically re‑run the simulation whenever key configuration parameters change (with basic debouncing so you don’t spam runs).
- **Run Simulation** button  
  Executes a high‑fidelity single‑lap simulation using the current settings, logs to `simulation_log.txt`, and updates all result views.

### Results & Analysis tab

Shows a high‑level view suitable for quick engineering decisions:

- **Summary metrics**
  - Total lap time
  - Final battery SOC
  - Total energy harvested per lap
- **Segment‑by‑segment breakdown table**
  - For each segment: time, exit speed, throttle %, brake %, SOC, MGU‑K deploy power, and harvest power.
- **Consolidated multi‑axis telemetry chart**
  - Single Plotly chart with:
    - Speed vs distance (primary y‑axis)
    - MGU‑K deploy and harvest power vs distance (secondary y‑axis)
    - SOC vs distance (secondary y‑axis)
  - Hover‑synchronised and rendered directly in Streamlit (no external HTML files).

### Visualisation tab

More detailed look at the telemetry, split into four interactive Plotly charts:

1. **Speed profile**  
   Speed vs distance.
2. **MGU‑K deploy & harvest power**  
   Deploy power and harvest power traces.
3. **Battery SOC**  
   SOC (MJ) vs distance.
4. **Throttle & brake pedal**  
   Throttle % and brake % vs distance.

### Debug Logs tab

- Live viewer for `simulation_log.txt` with a **Refresh Logs** button.
- Includes:
  - High‑level run events (config loads, constructor/strategy used).
  - `simulate_lap` progress and per‑segment timing.
  - Diagnostics from config merge and validation (e.g., warnings when critical sections are missing).

### Presets

- Save the current configuration to a YAML preset file.
- Load any preset back into the app from the sidebar.
- Useful for:
  - Comparing different strategies or constructors.
  - Keeping “reference” real‑world runs (e.g., tuned to a specific quali lap).

### Validation & safety

- Built‑in config validation checks:
  - Runtime section & default constructor existence.
  - ERS constraints (SOC, MGU‑K power, efficiencies, duty threshold, per‑lap harvest).
  - Basic environment sanity ranges (air / track temperature).  
- Invalid configurations are rejected with clear error messages before the physics engine runs.

---

## Physics & Optimization Overview

### Core physics model

Implemented in `model/core.py`:

- **Tyre grip**
  - Base grip per compound from config, adjusted for track temperature offset and simple warm‑up model.
- **Drag & downforce**
  - Drag is quadratic in speed with DRS effects on straights.
  - Downforce / friction circle limits maximum corner speed using tyre lateral μ and corner radius.
- **ERS deploy / harvest**
  - MGU‑K deploy power capped by both `P_K_max_kW` and available SOC.
  - Speed‑derated deploy at high velocities (realistic 290–340 km/h taper).
  - Harvest model triggered by braking and corner types, limited by efficiency and power caps.
- **Thermal fade**
  - When cumulative deploy exceeds a duty threshold, effective power fades towards a floor.
- **SOC floor penalty**
  - If SOC drops below a strategy‑specific floor, a time penalty is added to simulate lift‑and‑coast / compromised lines.

All of this is integrated with a simple Euler scheme over each track segment.

### Auto‑optimizer (optional)

Implemented in `model/optimization.py`:

- Uses `scipy.optimize.minimize` with L‑BFGS‑B to tune:
  - `deploy_factor_base`
  - `harvest_factor_base`
- Bounds for both are taken from the `auto_optimizer` entry in the strategies section of the runtime config.
- Objective:
  - Minimise lap time plus a penalty if final SOC falls below the strategy’s SOC floor threshold.
- The resulting optimal strategy is passed back into `simulate_lap` for a final “best lap” and full telemetry.

---
## Project strcuture
```text
  F1LapForge/
  ├── app.py                     # Main Streamlit entry point + tabs
  ├── config_runtime.yaml        # Default vehicle, ERS, strategy config
  ├── tracks_2026.yaml           # Circuit segment data
  ├── model/
  │   ├── core.py                # Physics engine (segment_dynamics + simulate_lap)
  │   └── optimization.py        # Gradient-based auto-optimizer
  ├── ui/
  │   ├── config_panel.py        # Sidebar parameter editor
  │   ├── results_panel.py       # Metrics, table, Plotly charts
  │   └── presets.py             # Save/load YAML presets
  ├── utils/
  │   ├── yaml.py                # YAML load/save/merge helpers
  │   ├── format.py              # Time formatting utilities
  │   └── validation.py          # Input validation
  ├── simulation_log.txt         # Auto-generated execution log
  └── requirements.txt
```
---

## Installation & Running

1. Clone the repository
   ```bash
   git clone https://github.com/ak-dev-os/F1LapForge.git
   cd F1LapForge
2. Create virtual environment (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate     # Linux / macOS
   venv\Scripts\activate        # Windows
3. Install dependencies
   ```bash
   pip install -r requirements.txt
5. Run the application
   ```bash
   streamlit run app.py   

---

## Reporting bugs or requesting features

1. Go to: <https://github.com/ak-dev-os/F1LapForge/issues>  
2. Click **New issue**.  
3. Choose the appropriate template (**Bug report** / **Feature request**) or write a clear description including:
   - Steps to reproduce  
   - Expected vs actual behavior  
   - Screenshots, log excerpts, and environment information  

### Code contributions

1. Fork the repository.  
2. Create your feature branch:  
   ```bash
   git checkout -b feature/amazing-feature
3. Commit your changes
   ```bash
   git commit -m "Add amazing feature"
4. Push to the branch
   ```bash
   git push origin feature/amazing-feature
5. Raise Pull Request
