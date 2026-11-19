# Jwana CircuitLab Pro — Updated Control Systems Simulator

This is an **upgrade to the simulator you already launched successfully**, not an unrelated application. It retains the same six series/parallel RC, RL and RLC models and circuit schematics. It adds the professor's requested analysis of first/second-order dynamics, pole locations, two-parameter 3D voltage/current surfaces, system states, frequency sweep and multiple input signals.

## Installation on Windows

1. If the old simulator is running, select its PowerShell window and press `Ctrl+C` to stop it.
2. Extract the ZIP in Downloads. Open the inner `Jwana_Circuit_Simulator_PRO_UPGRADE` folder until you can see `app.py`.
3. Click the **address bar at the top** of File Explorer, type `powershell`, press Enter.
4. Run `py -m pip install -r requirements.txt` and wait for installation to finish.
5. Run `py -m streamlit run app.py` and open the URL printed in PowerShell (normally `http://localhost:8501`).
6. Select the circuit in the left sidebar. Adjust the R, L, C sliders and explore the six main tabs.

If app.py is not found, the PowerShell window is in the wrong folder. Use `dir` and open the directory containing the file before starting the app.

## Main tabs

| Tab | What it does |
|---|---|
| Circuit & response | Six circuit drawings and separate voltage/current plots; shows input waveform and state trajectories |
| System order & poles | First order τ, second order ζ and ωn, dynamic poles, pole movements, output transfer functions |
| 3D time surface | Time vs one component value vs any output voltage or current |
| 3D two-variable sweep | Choose **two distinct parameters**, select voltage/current output(s), and a metric; generate a 3D surface for each output, with an **ALL** option |
| Frequency & sweeping | Bode magnitude, phase, and 3D frequency-vs-component surfaces; chirp time input also supported |
| All data & export | Download all element voltages/currents and states as CSV, and circuit settings as JSON |

## Suggested live demonstration for your professor

### First-order RC: vary two variables

- Select **RC** then **Series**, DC step 10 V, R = 4 Ω, C = 100 mF, initial capacitor voltage 1.2 V.
- In **System order & poles**, identify λ = −1/(RC) = −2.5 s⁻¹ and τ = RC = 0.4 s.
- In **3D two-variable sweep**, set X = R, Y = C, measured output = Capacitor Voltage (V), metric = Value at selected time, observation t = 1 s.
- Rotate the graph to see how R and C affect the capacitor charging response.

### First-order RL

- Select **RL**, **Series**, R = 4 Ω, L = 1 H. Explain τ = L/R = 0.25 s, pole −4 s⁻¹.
- Choose X = R and Y = L and inductor current as the 3D output.

### Second-order RLC

- Select **RLC**, **Series**, R = 4 Ω, L = 1 H, C = 100 mF.
- In **System order & poles**, identify ωn = 1/sqrt(LC) ≈ 3.1623 rad/s and ζ = (R/2)*sqrt(C/L) ≈ 0.6325; the poles are −2 ± j 2.449.
- Modify R to see pole movement and damping change. Use **Frequency & sweeping** for resonance-related behavior.

### All voltages and currents

- In **3D two-variable sweep**, tick **Select ALL element outputs**. The simulator will produce one 3D surface for each current and voltage. Output labels identify units (V or A) separately.

### Swept-sine transient

- Select **Chirp sweep** in the sidebar and adjust start/end frequencies. The first tab shows the actual voltage/current response for that time-varying input. The Frequency & sweeping tab separately displays theoretical sinusoidal steady-state response.

## Reproducibility and limitations

- State equation: `dx/dt = A @ x + B * u(t)`; output: `y = C @ x + D * u(t)`.
- **Series**: ideal voltage source in series with R/L/C; **Parallel**: finite positive source resistance Rs feeding parallel branches.
- All parameter values are in SI units internally; C is displayed as mF in the interface and converted to farads.
- The 3D two-component surface varies the selected components and resolves the physical state equations for each grid point.
- Numerical integration uses SciPy LSODA; high-frequency choices require enough samples per cycle.
- This simulator covers nine useful input families; it does not claim to represent every imaginable mathematical source.
- Plots represent ideal components; nonlinear saturation, stray resistance and real device parasitics are not modeled.

## Source code

`app.py` is the Streamlit UI, `models.py` keeps the original circuit state equations, `diagram.py` draws the circuits, and `analysis_engine.py` implements source signals, all element outputs, sweeps and pole analysis. `test_advanced.py` contains automated tests.

## Technical references

- [SciPy `solve_ivp`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)
- [SciPy `ss2tf`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ss2tf.html)
- [Plotly 3D surfaces](https://plotly.com/python/3d-surface-plots/)
- [Streamlit Plotly charts](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart)
