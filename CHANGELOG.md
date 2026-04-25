# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
### Changed
### Fixed

---

## [0.2.7] — 2026-04-25

### Added

#### Visualisation
- `Light` palette class — mirror of `Dark` for white-background environments (presentations, reports)
- `mpl_theme(theme="dark"|"light")` — `mpl_theme()` now accepts a `theme` argument; default unchanged (`"dark"`)
- `save=` parameter on `CartPoleView`, `PendulumView`, `MassSpringDamperView` — records the session to a file on close
- `_trail_point(x)` hook on `SimViewBase` — concrete views override to return the 3D position appended to the trail; `CartPoleView` traces pole tip, `PendulumView` traces pole tip, `MassSpringDamperView` traces mass centre

#### Examples
- `examples/simulators/05_cartpole2d_features.py` — demonstrates `Light` palette, `mpl_theme("light")`, headless `simulate()`, `animate(save=)`, and custom LQR
- `examples/simulators/06_simview_advanced.py` — demonstrates camera presets, trajectory trail, and `save=` for Qt SimViews

#### Documentation
- `website/docs/api/viz.md` — added `CartPole2DView`, `Light`, updated `mpl_theme()` signature, `save=` on all SimView constructors, `set_camera_preset()` and `toggle_trail()` on `SimViewBase`
- `website/docs/guide/viz/overview.md` — restructured around 2D vs 3D tiers with comparison table
- `website/docs/guide/viz/simview.md` — new sections: camera presets, trajectory trail, saving animations, light theme
- `website/docs/guide/simulators/` — four new pages: Overview, Mass-Spring-Damper, Inverted Pendulum, Cart-Pole
- `examples/simulators/04_integrator_benchmark.py` — Euler / RK4 / RK45 wall-clock time and RMS error comparison

---

## [0.2.6] — 2026-04-25

### Added

#### Simulator enhancements
- `SimulatorBase.step()` now returns `info["failed"]` via overridable `failed(x)` hook (default `False`)
- `CartPoleSim.failed()` — triggers when `|p| > 4.8 m` or `|θ| > π/3 rad`
- `InvertedPendulumSim.failed()` — triggers when `|θ| > π/2 rad`
- `CartPoleSim(linearised=True)` — switches dynamics to linearised model around upright equilibrium

#### PlantAgent
- `PlantAgent` now accepts `Union[StateSpace, SimulatorBase]`; pass `dt=` when using a nonlinear simulator

#### Visualisation
- `CartPole2DView` — lightweight matplotlib-only 2D animation: auto-LQR, pluggable controller, `simulate()` / `animate(save=...)` / `run()` API
- `SimViewBase.set_camera_preset(name)` — switch 3D camera to `"iso"`, `"top"`, `"side"`, or `"follow"`
- `SimViewBase.toggle_trail()` and `_append_trail_position()` — trajectory trail state management
- `synapsys.viz` now imports `simview` lazily so `CartPole2DView` remains available on headless environments

#### Tests
- 541 tests (up from 501), 100% coverage maintained

---

## [0.2.5] — 2026-04-25

### Added

#### Physical Simulators (`synapsys/simulators/`)
- `SimulatorBase` — abstract base for nonlinear continuous-time simulators: Euler/RK4/RK45 integrators, thread-safe `step(u, dt)`, sensor noise, input disturbance, numerical `linearize()` via central finite differences returning a `StateSpace`.
- `MassSpringDamperSim` — 1-DOF linear MSD; linearise validates against known analytical A/B/C/D.
- `InvertedPendulumSim` — nonlinear inverted pendulum on fixed pivot with `unstable_pole()` utility.
- `CartPoleSim` — 4-state Lagrangian cart-pole with partial observation (position + angle).
- All simulators: thread-safe `set_params()`, `params` property, Euler/RK4/RK45 selectable.

#### SimView real-time 3D UI (`synapsys/viz/simview/`)
- `SimViewBase` — Qt+PyVista base class: render loop, live matplotlib telemetry panels, parameter sliders, play/pause/reset controls.
- `MSDView`, `PendulumView`, `CartPoleView` — per-simulator 3D scenes with live telemetry.
- `synapsys/viz/palette.py` — centralised color palette for consistent UI theming.

#### Examples
- `examples/simulators/01_mass_spring_damper.py` — step response, LQR design, linearisation validation.
- `examples/simulators/02_inverted_pendulum.py` — LQR stabilisation with noise and disturbance injection.
- `examples/simulators/03_cartpole.py` — Lagrangian dynamics, partial observation, LQR control.

#### Website
- Homepage `SimulatorsShowcase` section with GIF cards (MSD, pendulum, cart-pole) and solid backgrounds.
- `HomeBlogSection` carousel component.
- SimView documentation pages: overview, guide, API reference (EN + PT).
- Roadmap updated with simulator milestone.

### Changed

- `pyproject.toml`: added ruff per-file-ignores for `synapsys/simulators/**`, `synapsys/viz/**`, `tests/simulators/**`; mypy `exclude = ["synapsys/viz/"]`; coverage `omit = ["synapsys/viz/*"]`.
- README: new SimView demo section with GIFs, updated features table, architecture tree, test count 287 → 501.
- Test suite: 287 → 501 tests; 100% coverage maintained.

---

## [0.2.4] — 2026-04-20

### Changed

#### Website & assets
- **New Synapse-S logo** — replaced logo with gold/navy Synapse-S design; added `logo_dark.svg`, `logo_light.svg` and `logo_dark.png` (1000×1000) variants.
- **Theme-adaptive logo** — navbar and homepage now swap between dark/light logo automatically via `srcDark` and `ThemedLogo` component.
- **Favicon** — regenerated `favicon.ico` (16/32/48 px) from new logo via cairosvg for crisp rendering.
- **LinkedIn icon** — neutralised colour to match GitHub icon (uses `currentColor`).
- **Author title** — updated to avoid redundant MSc label.

#### Docs
- **Quadcopter PT translation** — added "Controle de yaw alinhado à direção" section with math, edge-cases table, code snippet and updated Mermaid diagram.
- **v0.2.3 versioned snapshot** — backported yaw control docs to versioned EN + PT snapshot.

---

## [0.2.3] — 2026-04-20

### Added

#### Quadcopter MIMO example
- **Heading-aligned yaw control** — drone now rotates to face the direction of travel via `ψ_ref = atan2(ẏ, ẋ)`; yaw error wrapped to `[-π, π]`; holds current heading below 0.08 m/s to suppress hover noise.
- **IMPROVEMENTS.md** — roadmap of 6 planned enhancements (velocity feedforward, Kalman filter, non-linear RK4 dynamics, PPO RL fine-tuning, multi-drone ZMQ formation, wind disturbance model).
- Refreshed `quadcopter_3d.gif` and `quadcopter_telemetry.gif` with updated simulation.

---

## [0.2.2] — 2026-04-19

### Added

#### MessageBroker layer
- `synapsys/broker/` — high-level pub/sub bus decoupled from the low-level `TransportStrategy`.
  - `MessageBroker` — central bus; agents call `publish(topic, data)` / `subscribe(topic)` instead of raw read/write.
  - `Topic` — typed channel descriptor with name and size validation.
  - `SharedMemoryBackend` — zero-copy shared memory backend for single-host setups.
  - `ZMQBrokerBackend` — ZeroMQ PUB/SUB backend for multi-process and multi-machine deployments.
- `PlantAgent`, `ControllerAgent`, `HardwareAgent` — accept an optional `broker` parameter alongside the existing `transport` parameter.

#### Quality
- **100% line coverage** — 287 tests across all modules; `pytest --cov-fail-under=100` enforced in CI.
- **pre-commit hooks** — `ruff lint`, `ruff format`, `mypy` and `pytest` run automatically on every `git commit` (`.pre-commit-config.yaml`).
- **mypy strict** — all modules pass `mypy --strict` with 0 errors; `TYPE_CHECKING` guards eliminate circular imports in agent modules.

#### Documentation
- `README.md` — quadcopter and SIL GIFs, all package managers (`pip`, `uv`, `Poetry`, `conda`), updated architecture diagram (broker layer), 287-test / 100%-coverage stats, pre-commit badge, contributors section.
- `synapsys-lab/.github` profile README updated with drone GIFs, MIMO section, full install options and contributors grid.

### Fixed
- Lambda control laws in examples replaced with proper `def` functions (ruff E731).
- `zmq.py` `read()` return type narrowed from `Any` to `np.ndarray` (mypy strict).

---

## [0.2.1] — 2026-04-18

### Added

#### Quadcopter MIMO Example
- `examples/advanced/06_quadcopter_mimo/` — complete real-time simulation of a 12-state linearised quadcopter controlled by a residual Neural-LQR (`δu = −K·e + MLP(e)`).
- `quadcopter_dynamics.py` — physical constants, `build_matrices()`, `figure8_ref()`, LQR weight matrices `Q` and `R`.
- `06a_quadcopter_plant.py` — two-process SIL variant via `PlantAgent` + `SharedMemoryTransport`.
- `06b_neural_lqr_3d.py` — standalone simulation with:
  - **tkinter config GUI**: simulation time, hover altitude, reference trajectory (Figure-8 / Circle / Hover) and its parameters.
  - **PyVista 3D window** (50 Hz): drone mesh, trajectory trail, static reference curve, HUD overlay.
  - **matplotlib telemetry window** (10 Hz): x-y trajectory, altitude, Euler angles, control inputs.
  - **`--save` export mode**: runs fast (no real-time pacing) and saves `quadcopter_3d.gif` and `quadcopter_telemetry.gif` via PyVista off-screen + matplotlib PillowWriter.
- `pyvista>=0.43` added as `synapsys[viz]` optional dependency.
- Full EN + PT documentation with embedded GIF recordings.

### Fixed
- `synapsys/__init__.py` version synced to match `pyproject.toml` (was `0.1.0`, now `0.2.1`).

---

## [0.2.0] — 2026-04-18

### Added

#### MIMO Support
- `TransferFunctionMatrix` — MIMO transfer-function matrix `G(s)` of shape `(n_outputs × n_inputs)`, storing SISO `TransferFunction` elements at `G[i, j]`.
  - Full operator algebra: element-wise `+` (parallel), matrix-multiply `*` (series), negation `-`.
  - `to_state_space()` — block-diagonal minimal state-space realisation; zero-numerator elements are skipped to avoid scipy phantom states.
  - `poles()`, `zeros()`, `is_stable()`, `simulate()`, `step()`, `bode()`.
  - `from_arrays(num, den)` factory: supports shared denominator or per-element denominators.
- `tf()` MIMO dispatch — `tf(num, den)` with 2-D `num` now returns a `TransferFunctionMatrix` (mirrors MATLAB `tf`).
- `feedback()` MIMO support — `feedback(G)` and `feedback(G, H)` now accept `StateSpace` and `TransferFunctionMatrix` plants, returning a `StateSpace` closed-loop model.
- Transmission zeros via Rosenbrock system-matrix pencil — replaces deprecated `scipy.signal.zpkdata`; correct for both SISO and MIMO state-space models.

#### Validation
- `lqr()` — added positive semi-definiteness check for `Q` (`eigvalsh` ≥ −1e-10); complements the existing Cholesky check on `R`.
- `feedback()` — added sample-time (`dt`) mismatch guard between plant `G` and sensor `H`.
- `series()` / `parallel()` — added guard against zero-argument calls.
- `tf()` — added `TypeError` guard for `None` numerator or denominator.
- `StateSpace.__mul__()` — added inner-dimension validation for series connection.
- `StateSpace.zeros()` — added non-square plant guard with descriptive error message.
- `StateSpace.to_transfer_function()` — added MIMO guard (raises `ValueError` for non-SISO plants).

#### Type Annotations
- `LTIModel.to_state_space()` and `LTIModel.to_transfer_function()` now declare covariant return types (`StateSpace` and `TransferFunction`) via `TYPE_CHECKING` imports, enabling accurate static analysis with mypy/pyright.

### Changed
- Test suite expanded from 74 to 184 tests; coverage increased from 86 % to 90 %.

### Known Limitations
- **No advanced frequency-domain tools** — `margin()`, `rlocus()`, `pole_placement()` planned for v0.3.
- **No state estimation** — Kalman filter and Luenberger observer planned for v0.3.
- **No hardware implementations** — `HardwareInterface` subclasses for real hardware planned for v0.5.
- **Race-condition caveat** — `SharedMemoryTransport` has no internal mutex; architect channels so that each process is the sole writer of its own channel.

---

## [0.1.0] — 2026-04-11

### Added

#### Core LTI Systems
- `TransferFunction` — SISO transfer function with full operator overloading (`+`, `*`, `/`, negation), poles, zeros, stability check, step response, and Bode diagram.
- `StateSpace` — continuous and discrete state-space models with `evolve()` for real-time simulation, pole/zero extraction, stability, step response, and Bode diagram.
- Operator interoperability between `TransferFunction` and `StateSpace` via the `LTIModel` abstract base class.

#### MATLAB-Compatible API (`synapsys.api`)
- `tf(num, den)` — construct a transfer function.
- `ss(A, B, C, D)` — construct a state-space model.
- `c2d(sys, dt, method)` — continuous-to-discrete conversion (ZOH, bilinear/Tustin, Euler forward, backward-diff).
- `step(sys)` — compute step response; returns `(t, y)`.
- `bode(sys)` — compute frequency response; returns `(omega, mag, phase)`.
- `feedback(P, C)` — unity or custom negative feedback interconnection.
- `series(G1, G2)` — series connection.
- `parallel(G1, G2)` — parallel connection.

#### Control Algorithms (`synapsys.algorithms`)
- `PID` — discrete PID controller with anti-windup (back-calculation), output saturation, and `reset()`.
- `lqr(A, B, Q, R)` — continuous-time LQR solver via the algebraic Riccati equation; returns gain matrix `K` and cost matrix `P`.

#### Multi-Agent Simulation (`synapsys.agents`)
- `BaseAgent` — abstract lifecycle agent (setup → step loop → teardown) backed by a daemon thread.
- `PlantAgent` — simulates a discrete `StateSpace` plant in real time, publishing `y` and consuming `u` each tick.
- `ControllerAgent` — executes an arbitrary control law `Callable[[ndarray], ndarray]` (PID, LQR, neural net, …) each tick.
- `SyncEngine` — two synchronisation modes: `LOCK_STEP` (barrier-based) and `WALL_CLOCK` (fixed-rate wall time).
- `ACLMessage` / `Performative` — lightweight FIPA ACL message structure for agent communication.

#### Transport Layer (`synapsys.transport`)
- `SharedMemoryTransport` — zero-copy IPC via OS shared memory (`multiprocessing.shared_memory`); supports multiple named channels in a single block.
- `ZMQTransport` — asynchronous PUB/SUB transport over ZeroMQ for distributed (multi-machine) simulation.
- `ZMQReqRepTransport` — synchronous REQ/REP transport for lock-step coordination over the network.
- `TransportStrategy` — abstract interface; implement to plug in custom transports (serial, OPC-UA, ROS 2, …).

#### Hardware Abstraction (`synapsys.hw`)
- `HardwareInterface` — abstract interface for FPGA, FPAA, and microcontroller backends (implementations planned for v0.5).

### Known Limitations

- **SISO only** — `TransferFunction` and `StateSpace` assume a single input and single output. MIMO support is planned for v0.2.
- **No advanced frequency-domain tools** — `margin()`, `rlocus()`, `pole_placement()`, and Padé delay approximation are not yet implemented (v0.2).
- **No state estimation** — Kalman filter and Luenberger observer are planned for v0.3.
- **No hardware implementations** — `HardwareInterface` subclasses for real hardware are planned for v0.5.
- **Race-condition caveat** — `SharedMemoryTransport` has no internal mutex; architect channels so that each process is the sole writer of its own channel.

[0.2.0]: https://github.com/synapsys-lab/synapsys/releases/tag/v0.2.0
[0.1.0]: https://github.com/synapsys-lab/synapsys/releases/tag/v0.1.0
