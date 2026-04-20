# Quadcopter Neural-LQR — Improvement Ideas

Roadmap of planned and candidate improvements for the `06_quadcopter_mimo` example.
Each idea is self-contained and can be implemented independently.

---

## A · Velocity feedforward on the reference

**Complexity:** Low  
**Files:** `quadcopter_dynamics.py`, `06b_neural_lqr_3d.py`

### Problem

The current control law tracks only position/attitude error:

```
e = x - x_ref    (x_ref has ẋ_ref = ẏ_ref = 0)
δu = −K · e
```

At higher trajectory speeds (ω > 0.4 rad/s) the drone lags behind the reference because the controller
only reacts to position error — it does not anticipate the required velocity.

### Proposed fix

Extend `x_ref` to include velocity components derived analytically from the trajectory:

```python
# figure-8 velocity feedforward
dx_ref = -A * omega * sin(omega*t) / denom + A * cos(omega*t) * 2*sin(omega*t)*cos(omega*t)*omega / denom**2
dy_ref =  A * omega * (cos(2*omega*t)*denom - sin(omega*t)*cos(omega*t)*(-2*sin(omega*t)*cos(omega*t)*omega)) / denom**2

x_ref[6] = dx_ref   # ẋ_ref
x_ref[7] = dy_ref   # ẏ_ref
```

### Expected gain

- Tracking error reduction ~40–60 % at ω = 0.5 rad/s
- No change to the controller structure — same LQR gain K

---

## B · Kalman filter state estimator

**Complexity:** Medium  
**New file:** `kalman_estimator.py`

### Problem

The simulation uses full, noise-free state feedback:

```
δu = −K · x_true
```

In a real system, only outputs are measurable (y = Cx) and they are corrupted by sensor noise.
This makes the current example non-representative of real hardware deployments.

### Proposed implementation

Add a **Discrete Kalman Filter** (linear, time-invariant) that estimates the full state from
simulated noisy measurements:

```python
class KalmanFilter:
    """
    Discrete-time Kalman filter for the linearised quadcopter.

    State:  x̂ ∈ ℝ¹²
    Output: y ∈ ℝ⁴  (x, y, z, ψ — GPS + magnetometer)
    """
    def __init__(self, A_d, B_d, C, Q_n, R_n, x0):
        self.A, self.B, self.C = A_d, B_d, C
        self.Q, self.R = Q_n, R_n     # process noise, measurement noise
        self.x_hat = x0.copy()
        self.P = np.eye(12)           # initial covariance

    def predict(self, u):
        self.x_hat = self.A @ self.x_hat + self.B @ u
        self.P = self.A @ self.P @ self.A.T + self.Q

    def update(self, y_meas):
        S = self.C @ self.P @ self.C.T + self.R
        K = self.P @ self.C.T @ np.linalg.inv(S)   # Kalman gain
        self.x_hat += K @ (y_meas - self.C @ self.x_hat)
        self.P = (np.eye(12) - K @ self.C) @ self.P
        return self.x_hat
```

**Noise model:**
- GPS: σ_xy = 0.05 m, σ_z = 0.03 m
- Magnetometer: σ_ψ = 0.02 rad
- IMU (velocities/rates): not directly measured — estimated by KF

**New telemetry panel:** `x_true` vs `x̂` overlay to visualise filter convergence.

---

## C · Non-linear full-envelope dynamics (Euler-Newton)

**Complexity:** High  
**New file:** `quadcopter_nonlinear.py`

### Problem

The linearised model is only valid for small angles (|φ|, |θ| ≤ 15°).
Any aggressive manoeuvre or large initial condition violates this assumption
and the simulation diverges from reality.

### Proposed implementation

Replace the linear `sys_d.evolve(x, u)` call with a non-linear Runge-Kutta integrator:

```python
def nonlinear_dynamics(x, u, params):
    """
    Full Euler-Newton rigid-body dynamics.

    State: x = [px, py, pz, phi, theta, psi, vx, vy, vz, p, q, r]
    Input: u = [F_total, tau_phi, tau_theta, tau_psi]
    """
    px, py, pz, phi, theta, psi, vx, vy, vz, p, q, r = x
    F, tau_p, tau_q, tau_r = u
    m, Ixx, Iyy, Izz, g = params

    # Rotation matrix (ZYX Euler)
    cphi, sphi = cos(phi), sin(phi)
    cth,  sth  = cos(theta), sin(theta)
    cpsi, spsi = cos(psi), sin(psi)

    # Position kinematics (body → world)
    dp = R_world @ np.array([vx, vy, vz])

    # Velocity dynamics (Newton, world frame)
    ddv = np.array([
        (cpsi*sth*cphi + spsi*sphi) * F/m,
        (spsi*sth*cphi - cpsi*sphi) * F/m,
        (cth*cphi) * F/m - g,
    ])

    # Attitude kinematics (Euler rates from body rates)
    T_inv = np.array([
        [1, sphi*tan(theta),  cphi*tan(theta)],
        [0, cphi,            -sphi           ],
        [0, sphi/cth,         cphi/cth       ],
    ])
    dangle = T_inv @ np.array([p, q, r])

    # Angular dynamics (Euler equations)
    domega = np.array([
        (tau_p - (Iyy - Izz)*q*r) / Ixx,
        (tau_q - (Izz - Ixx)*p*r) / Iyy,
        (tau_r - (Ixx - Iyy)*p*q) / Izz,
    ])

    return np.concatenate([dp, dangle, ddv, domega])

def rk4_step(x, u, dt, params):
    k1 = nonlinear_dynamics(x,            u, params)
    k2 = nonlinear_dynamics(x + dt/2*k1,  u, params)
    k3 = nonlinear_dynamics(x + dt/2*k2,  u, params)
    k4 = nonlinear_dynamics(x + dt*k3,    u, params)
    return x + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
```

**Implication for the controller:**  
The LQR gain K (computed on the linearised model) remains valid near hover.
For large deviations, the Neural-LQR MLP residual can learn the non-linear compensation.

---

## D · Online RL fine-tuning of the MLP residual

**Complexity:** High  
**New file:** `rl_trainer.py`

### Problem

The MLP residual is currently zeroed and never trained — the controller
always reduces to pure LQR. The architecture was designed for RL fine-tuning
but no training loop exists yet.

### Proposed implementation

Add a **PPO training loop** that runs between simulation episodes:

```python
# Reward function — penalise tracking error and control effort
def reward(e, delta_u):
    pos_err   = np.sum(e[:3]**2)            # position tracking
    att_err   = np.sum(e[3:6]**2)           # attitude error
    ctrl_cost = np.sum(delta_u**2) * 0.01   # control effort
    return -(pos_err + att_err + ctrl_cost)

# PPO update (simplified)
optimizer = torch.optim.Adam(net.residual.parameters(), lr=3e-4)

for episode in range(N_EPISODES):
    states, actions, rewards = rollout(env, net)
    advantages = compute_gae(rewards, values, gamma=0.99, lam=0.95)
    for _ in range(N_EPOCHS):
        loss = ppo_loss(states, actions, advantages, net, clip_eps=0.2)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
```

**Safety constraint:** A penalty term keeps the MLP output small, preserving the LQR baseline:

```python
regularization = 1e-3 * torch.sum(net.residual[-1].weight**2)
loss += regularization
```

**Curriculum:** Start with easy hover, gradually increase trajectory speed ω.

---

## E · Multi-drone formation with ZMQ

**Complexity:** High  
**New files:** `formation_controller.py`, `06c_multi_drone.py`

### Problem

The current example simulates a single drone. Multi-agent coordination —
a core feature of Synapsys — is not demonstrated at the drone level.

### Proposed architecture

Run **N drones** as independent processes communicating position via ZMQ:

```
Drone 0 (leader)     →  publishes  →  topic: "quad/0/state"
Drone 1 (follower)   →  subscribes →  topic: "quad/0/state"
                     →  publishes  →  topic: "quad/1/state"
Drone 2 (follower)   →  subscribes →  topics: "quad/0/state", "quad/1/state"
...
```

**Formation control law** (virtual structure):

```python
def formation_control(x_self, x_leader, offset, K_form):
    """
    offset: desired relative position [dx, dy, dz] in world frame
    K_form: formation gain (damped spring)
    """
    e_form = (x_leader[:3] + offset) - x_self[:3]
    return K_form @ e_form     # additive correction to reference
```

**Visualisation:** All N drones in the same PyVista scene with different colours and
a wireframe polyhedron showing the desired formation geometry.

---

## F · Wind and turbulence disturbance

**Complexity:** Low  
**Files:** `quadcopter_dynamics.py`, `06b_neural_lqr_3d.py`

### Problem

The simulation runs in ideal conditions. Adding wind tests the robustness
of the Neural-LQR (and motivates the MLP residual as a disturbance compensator).

### Proposed implementation

Add a stochastic wind model (Dryden turbulence, simplified):

```python
class WindModel:
    """
    Low-pass filtered Gaussian noise — Dryden turbulence (simplified).
    sigma: intensity (m/s), tau: time constant (s)
    """
    def __init__(self, sigma=0.3, tau=2.0, dt=0.01):
        self.alpha = dt / (tau + dt)   # first-order IIR coefficient
        self.sigma = sigma
        self.v = np.zeros(3)           # [vx, vy, vz] wind velocity

    def step(self):
        noise  = np.random.randn(3) * self.sigma
        self.v = (1 - self.alpha) * self.v + self.alpha * noise
        return self.v

# In the simulation loop:
wind = WindModel(sigma=0.3, tau=2.0)

def sim_step(x, delta_u):
    v_wind = wind.step()
    # Wind adds a force proportional to relative velocity (drag model)
    F_wind = -DRAG_COEFF * (x[6:9] - v_wind)   # world-frame drag
    x_next = rk4_step(x, delta_u, DT, params, F_wind)
    return x_next
```

**New telemetry panel:** wind velocity components vx_w, vy_w, vz_w overlaid on drone velocity.

**Motivation for the MLP:** Show that the LQR baseline degrades under wind
and the trained MLP residual can compensate — a clear visual argument for the Neural-LQR architecture.

---

## Implementation priority

| Idea | Value / Effort | Recommended order |
|---|---|---|
| **F** · Wind disturbance | High value, Low effort | 1st |
| **A** · Velocity feedforward | High value, Low effort | 2nd |
| **B** · Kalman filter | High value, Medium effort | 3rd |
| **C** · Non-linear dynamics | High value, High effort | 4th |
| **D** · RL fine-tuning | Very high value, High effort | 5th |
| **E** · Multi-drone formation | Very high value, High effort | 6th |
