import type { ReactElement } from 'react';
import Link from '@docusaurus/Link';
import Translate, { translate } from '@docusaurus/Translate';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import useBaseUrl from '@docusaurus/useBaseUrl';
import { useColorMode } from '@docusaurus/theme-common';

import Layout from '@theme/Layout';
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import CodeBlock from '@theme/CodeBlock';
import LibraryMap from '@site/src/components/LibraryMap';
import HomeBlogSection from '@site/src/components/HomeBlogSection';
import SimulatorsShowcase from '@site/src/components/SimulatorsShowcase';
import NeuralNetBackground from '@site/src/components/NeuralNetBackground';
import {
  BookOpen,
  Cpu,
  FlaskConical,
  LayoutList,
  GitBranch,
  ArrowRight,
  BrainCircuit,
  Package,
  type LucideIcon,
} from 'lucide-react';

const GITHUB = 'https://github.com/synapsys-lab/synapsys';
const PYPI   = 'https://pypi.org/project/synapsys/';

// ── Quick-navigation cards ───────────────────────────���────────────────────────
const NAV_CARDS: { Icon: LucideIcon; title: string; desc: string; href: string }[] = [
  {
    Icon: BookOpen,
    title: translate({ id: 'home.nav.start.title',   message: 'Getting Started' }),
    desc:  translate({ id: 'home.nav.start.desc',    message: 'Installation, quickstart and first simulation.' }),
    href:  '/docs/getting-started/installation',
  },
  {
    Icon: LayoutList,
    title: translate({ id: 'home.nav.guide.title',   message: 'User Guide' }),
    desc:  translate({ id: 'home.nav.guide.desc',    message: 'LTI models, algorithms, agents and transport.' }),
    href:  '/docs/guide/core/transfer-function',
  },
  {
    Icon: Cpu,
    title: translate({ id: 'home.nav.api.title',     message: 'API Reference' }),
    desc:  translate({ id: 'home.nav.api.desc',      message: 'Complete reference for every public class and function.' }),
    href:  '/docs/api/core',
  },
  {
    Icon: FlaskConical,
    title: translate({ id: 'home.nav.examples.title', message: 'Examples' }),
    desc:  translate({ id: 'home.nav.examples.desc',  message: 'Step response, PID loop, LQR, real-time agents.' }),
    href:  '/docs/examples',
  },
];

// ── Module status table ───────────────────────────────────────────────────────
const MODULES = [
  { pkg: 'synapsys.core',      desc: 'TransferFunction, StateSpace, ZOH discretisation',   status: 'Stable' },
  { pkg: 'synapsys.api',       desc: 'MATLAB-compatible layer: tf(), ss(), step(), bode()', status: 'Stable' },
  { pkg: 'synapsys.algorithms', desc: 'Discrete PID with anti-windup, LQR (ARE solver)',   status: 'Stable' },
  { pkg: 'synapsys.agents',    desc: 'PlantAgent, ControllerAgent, SyncEngine',             status: 'Functional' },
  { pkg: 'synapsys.transport', desc: 'SharedMemory (zero-copy), ZMQ PUB/SUB & REQ/REP',    status: 'Functional' },
  { pkg: 'synapsys.viz',        desc: '3D sim views plug-and-play: CartPoleView, PendulumView, MassSpringDamperView', status: 'Functional' },
  { pkg: 'synapsys.hw',        desc: 'HardwareInterface, MockHardwareInterface (HIL)',      status: 'Interface' },
  { pkg: 'synapsys.mpc',       desc: 'Model Predictive Control',                            status: 'Planned' },
];

const STATUS_CLASS: Record<string, string> = {
  Stable:     'badge--stable',
  Functional: 'badge--functional',
  Interface:  'badge--interface',
  Planned:    'badge--planned',
};

// ── Sub-components ──────────────────────────────��──────────────────────────��──
function NavCard({ Icon, title, desc, href }: { Icon: LucideIcon; title: string; desc: string; href: string }): ReactElement {
  return (
    <Link to={href} className="nav-card">
      <span className="nav-card__icon"><Icon size={20} strokeWidth={1.75} /></span>
      <span className="nav-card__body">
        <span className="nav-card__title">{title} <ArrowRight size={13} className="nav-card__arrow" /></span>
        <span className="nav-card__desc">{desc}</span>
      </span>
    </Link>
  );
}

// ── Theme-aware logo ──────────────────────────────────────────────────────────
function ThemedLogo(): ReactElement {
  const { colorMode } = useColorMode();
  const logoUrl = useBaseUrl(colorMode === 'dark' ? '/img/logo_dark.svg' : '/img/logo_light.svg');
  return <img src={logoUrl} alt="Synapsys logo" className="doc-header__logo" />;
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Home(): ReactElement {
  const { siteConfig } = useDocusaurusContext();

  return (
    <Layout
      title={siteConfig.title}
      description={translate({
        id: 'home.meta.description',
        message: 'Python control systems library — LTI models, PID, LQR and distributed multi-agent simulation',
      })}
    >

      <NeuralNetBackground />

      {/* ── Header ────────────────────────────────────────────────────────── */}
      <header className="doc-header">
        <div className="doc-header__inner">
          <div className="doc-header__cols">

            {/* ── Logo column ── */}
            <div className="doc-header__logo-col">
              <ThemedLogo />
            </div>

            {/* ── Content column ── */}
            <div className="doc-header__content-col">
              <div className="doc-header__meta">
                <a href={PYPI} className="doc-badge doc-badge--pypi" target="_blank" rel="noreferrer">v0.2.6 · PyPI</a>
                <span className="doc-badge doc-badge--neutral">Python 3.10+</span>
                <span className="doc-badge doc-badge--neutral">MIT</span>
                <a href={`${GITHUB}/actions`} className="doc-badge doc-badge--neutral" target="_blank" rel="noreferrer">CI passing</a>
              </div>

              <h1 className="doc-header__title">{siteConfig.title}</h1>

              <p className="doc-header__tagline">
                <Translate id="home.header.tagline">
                  A Python library for modelling, analysis and real-time simulation of linear
                  control systems. Provides a MATLAB-compatible API over SciPy, a multi-agent
                  simulation framework, and a pluggable transport layer (shared memory / ZMQ)
                  for MIL → SIL → HIL workflows.
                </Translate>
              </p>

              <div className="install-cols">
                <div className="install-col">
                  <span className="install-col__label">pip</span>
                  <code className="install-col__cmd">pip install synapsys</code>
                </div>
                <div className="install-col">
                  <span className="install-col__label">uv</span>
                  <code className="install-col__cmd">uv add synapsys</code>
                </div>
                <div className="install-col">
                  <span className="install-col__label">dev</span>
                  <code className="install-col__cmd">uv sync --extra dev</code>
                </div>
              </div>

              <div className="doc-header__actions">
                <Link className="btn btn--primary" to="/docs/getting-started/installation">
                  <Translate id="home.header.cta.docs">Documentation</Translate>
                </Link>
                <Link className="btn btn--outline" to={GITHUB}>
                  <GitBranch size={15} /> GitHub
                </Link>
                <Link className="btn btn--outline" href={PYPI} target="_blank" rel="noreferrer">
                  <Package size={15} /> PyPI
                </Link>
              </div>
            </div>

          </div>
        </div>
      </header>

      {/* ── Navigation cards ──────────────────────────────────────────────── */}
      <section className="nav-cards__section">
        <div className="nav-cards__grid">
          {NAV_CARDS.map((c) => (
            <NavCard key={c.href} {...c} />
          ))}
        </div>
      </section>

      {/* ── Quick example ─────────────────────────────────────────────────── */}
      <section className="content-section">
        <div className="content-section__inner">
          <h2 className="content-section__title">
            <Translate id="home.example.title">Overview</Translate>
          </h2>
          <p className="content-section__lead">
            <Translate id="home.example.desc">
              Synapsys covers the full control-design workflow — from continuous-time
              LTI modelling to discrete real-time closed-loop simulation — with a
              consistent API across all stages.
            </Translate>
          </p>

          <Tabs>
            <TabItem value="lti" label="LTI Models">
              <CodeBlock language="python" title="Transfer functions and state-space — synapsys.api">
{`from synapsys.api import tf, ss, step, bode, feedback, c2d

# Transfer function:  G(s) = ωn² / (s² + 2ζωnˢ + ωn²)
wn, zeta = 10.0, 0.5
G = tf([wn**2], [1, 2*zeta*wn, wn**2])

# Closed-loop (negative feedback)
T = feedback(G)

# Frequency and time-domain analysis
w, mag, phase = bode(G)
t, y          = step(T)

# Zero-order-hold discretisation at 200 Hz
Gd = c2d(G, dt=0.005)`}
              </CodeBlock>
            </TabItem>

            <TabItem value="pid" label="PID / LQR">
              <CodeBlock language="python" title="Control algorithms — synapsys.algorithms">
{`from synapsys.algorithms import PID, lqr
import numpy as np

# Discrete PID with anti-windup saturation
pid = PID(Kp=3.0, Ki=0.5, Kd=0.1, dt=0.01,
          u_min=-10.0, u_max=10.0)
u = pid.compute(setpoint=5.0, measurement=y)

# LQR — solves the continuous algebraic Riccati equation
#   minimises  J = ∫ (x'Qx + u'Ru) dt
A = np.array([[ 0.,  1.], [-wn**2, -2*zeta*wn]])
B = np.array([[0.], [wn**2]])
K, P = lqr(A, B, Q=np.eye(2), R=np.eye(1))
# Control law:  u = −Kx`}
              </CodeBlock>
            </TabItem>

            <TabItem value="sim" label="Real-Time Simulation">
              <CodeBlock language="python" title="Multi-agent closed loop — synapsys.agents">
{`from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, ControllerAgent, SyncEngine, SyncMode
from synapsys.algorithms import PID
from synapsys.transport import SharedMemoryTransport
import numpy as np

# Discretise G(s) = 1/(s+1)  at 100 Hz
plant_d = c2d(ss([[-1]], [[1]], [[1]], [[0]]), dt=0.01)

# Shared-memory bus — zero-copy, latency < 1 µs
with SharedMemoryTransport("demo", {"y": 1, "u": 1}, create=True) as bus:
    bus.write("y", np.zeros(1)); bus.write("u", np.zeros(1))

    pid = PID(Kp=4.0, Ki=1.0, dt=0.01)
    law = lambda y: np.array([pid.compute(setpoint=3.0, measurement=y[0])])

    sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
    PlantAgent("plant", plant_d, bus, sync).start(blocking=False)
    ControllerAgent("ctrl",  law,     bus, sync).start(blocking=False)`}
              </CodeBlock>
            </TabItem>

            <TabItem value="ai" label="AI Integration">
              <CodeBlock language="python" title="Neural-LQR — physics-informed PyTorch controller — synapsys.utils + torch">
{`import torch, torch.nn as nn, numpy as np
from synapsys.utils import StateEquations
from synapsys.algorithms import lqr
from synapsys.agents import ControllerAgent, SyncEngine, SyncMode
from synapsys.transport import SharedMemoryTransport

# ── 1. Build 2-DOF mass-spring-damper via named equations ──────────────────
m, c, k = 1.0, 0.1, 2.0
eqs = (
    StateEquations(states=["x1", "x2", "v1", "v2"], inputs=["F"])
    .eq("x1", v1=1).eq("x2", v2=1)
    .eq("v1", x1=-2*k/m, x2=k/m, v1=-c/m)
    .eq("v2", x1=k/m, x2=-2*k/m, v2=-c/m, F=k/m)
)

# ── 2. Compute LQR optimal gains (solves Algebraic Riccati Equation) ───────
K, _ = lqr(eqs.A, eqs.B, Q=np.diag([1., 10., .5, 1.]), R=np.eye(1))
# K = [−0.38, 2.23, 0.42, 1.75]  →  u* = −K·x + Nbar·r

# ── 3. MLP initialized with LQR gains (physics-informed) ──────────────────
class NeuralLQR(nn.Module):
    def __init__(self, K, Nbar):
        super().__init__()
        self.Nbar = Nbar
        self.net = nn.Sequential(
            nn.Linear(4, 32), nn.Tanh(),  # hidden layers — trainable by RL
            nn.Linear(32, 16), nn.Tanh(),
            nn.Linear(16, 1),             # output layer ← LQR gains
        )
        with torch.no_grad():
            self.net[4].weight.data = torch.tensor(-K.reshape(1, -1))
    def forward(self, x):
        return self.net(x) + self.Nbar   # u = MLP(x) + Nbar·r

model = NeuralLQR(K, Nbar=3.535).eval()

# ── 4. Plug into ControllerAgent — works with any nn.Module ───────────────
def control_law(state: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        u = model(torch.tensor(state, dtype=torch.float32).unsqueeze(0))
    return np.clip(u.numpy().flatten(), -20.0, 20.0)

transport = SharedMemoryTransport("sil_2dof", {"state": 4, "u": 1}, create=False)
agent = ControllerAgent("neural_lqr", control_law, transport,
                        SyncEngine(SyncMode.WALL_CLOCK, dt=0.01))
agent.start(blocking=True)   # or blocking=False for real-time plot`}
              </CodeBlock>
            </TabItem>
          </Tabs>
        </div>
      </section>

      {/* ── MIL → HIL pipeline ─────────────────────────────────────────────── */}
      <section className="content-section content-section--alt">
        <div className="content-section__inner content-section__inner--narrow">
          <h2 className="content-section__title">
            <Translate id="home.hil.title">Simulation Fidelity Ladder</Translate>
          </h2>
          <p className="content-section__lead">
            <Translate id="home.hil.desc">
              Synapsys is designed for incremental fidelity increases.
              Only the transport layer changes — the controller algorithm remains identical
              across all three stages.
            </Translate>
          </p>
          <div className="pipeline">
            <div className="pipeline__stage">
              <span className="pipeline__label">MIL</span>
              <span className="pipeline__name"><Translate id="home.hil.mil.name">Model-in-the-Loop</Translate></span>
              <span className="pipeline__detail"><Translate id="home.hil.mil.detail">SharedMemoryTransport · PlantAgent</Translate></span>
            </div>
            <ArrowRight className="pipeline__arrow" size={18} />
            <div className="pipeline__stage">
              <span className="pipeline__label">SIL</span>
              <span className="pipeline__name"><Translate id="home.hil.sil.name">Software-in-the-Loop</Translate></span>
              <span className="pipeline__detail"><Translate id="home.hil.sil.detail">ZMQTransport · separate process</Translate></span>
            </div>
            <ArrowRight className="pipeline__arrow" size={18} />
            <div className="pipeline__stage">
              <span className="pipeline__label">HIL</span>
              <span className="pipeline__name"><Translate id="home.hil.hil.name">Hardware-in-the-Loop</Translate></span>
              <span className="pipeline__detail"><Translate id="home.hil.hil.detail">HardwareAgent · real device</Translate></span>
            </div>
          </div>
          <p className="pipeline__note">
            <Translate id="home.hil.note.prefix">See the </Translate>
            <Link to="/docs/guide/agents/hil-sil"><Translate id="home.hil.note.link">HIL / SIL guide</Translate></Link>
            <Translate id="home.hil.note.suffix"> for a step-by-step migration example.</Translate>
          </p>
        </div>
      </section>

      {/* ── AI Integration showcase — Quadcopter MIMO ────────────────────── */}
      <section className="content-section">
        <div className="content-section__inner">
          <h2 className="content-section__title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BrainCircuit size={22} strokeWidth={1.75} />
            <Translate id="home.ai.title">AI + Control Systems — Quadcopter MIMO Demo</Translate>
          </h2>
          <p className="content-section__lead">
            <Translate id="home.ai.desc">
              Any PyTorch, Keras or JAX model plugs directly into a ControllerAgent via a single
              np.ndarray → np.ndarray callback. Below: a 12-state MIMO quadcopter controlled by a
              residual Neural-LQR (δu = −K·e + MLP(e)) — the MLP starts zeroed so the system
              launches as pure LQR and can be fine-tuned via RL without losing stability.
            </Translate>
          </p>

          <div className="ai-showcase">
            <div className="ai-showcase__gifs">
              <div className="ai-showcase__figure">
                <img
                  src={useBaseUrl('/img/examples/06_quadcopter_3d.gif')}
                  alt="Real-time 3D animation of the quadcopter tracking a figure-8 trajectory"
                  className="ai-showcase__img"
                />
                <p className="ai-showcase__caption">
                  <Translate id="home.ai.quad3d.caption">
                    PyVista 3D window (50 Hz) — drone mesh, trajectory trail, reference curve and live HUD.
                  </Translate>
                </p>
              </div>

              <div className="ai-showcase__figure">
                <img
                  src={useBaseUrl('/img/examples/06_quadcopter_telemetry.gif')}
                  alt="Live telemetry: top-down x-y trajectory, altitude, Euler angles and control inputs"
                  className="ai-showcase__img"
                />
                <p className="ai-showcase__caption">
                  <Translate id="home.ai.quadtelem.caption">
                    matplotlib telemetry (10 Hz) — x-y position, altitude, Euler angles and control deviations δu.
                  </Translate>
                </p>
              </div>
            </div>

            <div className="ai-showcase__cards">
              {[
                {
                  id: "residual",
                  title: 'Residual Neural-LQR',
                  desc: 'δu = −K·e + MLP(e). Output layer zeroed at init → starts as pure LQR. The residual is trained later via RL or imitation learning.',
                },
                {
                  id: "mimo",
                  title: '12-State MIMO Plant',
                  desc: 'Linearised hover model (x, y, z, φ, θ, ψ, ẋ, ẏ, ż, p, q, r) built with ss() + c2d(). LQR gain K∈ℝ⁴ˣ¹² from lqr().',
                },
                {
                  id: "pytorch",
                  title: 'PyTorch / Keras Ready',
                  desc: 'The controller is a plain Python callable. Swap in any nn.Module — LSTM, Transformer, diffusion policy — without changing the simulation loop.',
                },
                {
                  id: "distributed",
                  title: 'Distributed & Real-Time',
                  desc: 'Plant and controller can run in separate processes or machines via SharedMemoryTransport or ZMQTransport — same API, zero code changes.',
                },
              ].map((card) => (
                <div key={card.id} className="ai-showcase__card">
                  <span className="ai-showcase__card-title">{translate({ id: `home.ai.card.${card.id}.title`, message: card.title })}</span>
                  <span className="ai-showcase__card-desc">{translate({ id: `home.ai.card.${card.id}.desc`, message: card.desc })}</span>
                </div>
              ))}
            </div>
          </div>

          <p className="pipeline__note" style={{ marginTop: '1.5rem' }}>
            <Translate id="home.ai.note.prefix">Full walkthrough: </Translate>
            <Link to="/docs/examples/advanced/quadcopter-mimo">
              <Translate id="home.ai.note.link">Quadcopter MIMO Neural-LQR example →</Translate>
            </Link>
          </p>
        </div>
      </section>

      {/* ── 3D Simulators Showcase ────────────────────────────────────────── */}
      <section className="content-section content-section--alt">
        <div className="content-section__inner">
          <h2 className="content-section__title">
            <Translate id="home.sims.title">3D Simulation Views</Translate>
          </h2>
          <p className="content-section__lead">
            <Translate id="home.sims.lead">
              Janelas de simulação 3D prontas para usar — conecte qualquer controlador
              (LQR, PID, rede neural, agente RL) com uma única linha de código.
            </Translate>
          </p>
          <SimulatorsShowcase />
        </div>
      </section>

      {/* ── Blog Carousel ─────────────────────────────────────────────────── */}
      <HomeBlogSection />

      {/* ── Library map ───────────────────────────────────────────────────── */}
      <section className="content-section">
        <div className="content-section__inner">
          <h2 className="content-section__title">
            <Translate id="home.libmap.title">Full Library Map</Translate>
          </h2>
          <p className="content-section__lead">
            <Translate id="home.libmap.desc">
              Nine focused packages — from LTI mathematics to real-time hardware.
              Click any card to jump to the API reference.
            </Translate>
          </p>
          <LibraryMap />
        </div>
      </section>

      {/* ── Package Overview ──────────────────────────────────────────────── */}
      <section className="content-section content-section--alt">
        <div className="content-section__inner">
          <h2 className="content-section__title">
            <Translate id="home.modules.title">Package Overview</Translate>
          </h2>
          <table className="module-table">
            <thead>
              <tr>
                <th><Translate id="home.modules.col1">Package</Translate></th>
                <th><Translate id="home.modules.col2">Contents</Translate></th>
                <th><Translate id="home.modules.col3">Status</Translate></th>
              </tr>
            </thead>
            <tbody>
              {MODULES.map((m) => (
                <tr key={m.pkg}>
                  <td><code>{m.pkg}</code></td>
                  <td className="module-table__desc">{translate({ id: `home.modules.${m.pkg}.desc`, message: m.desc })}</td>
                  <td><span className={`status-badge ${STATUS_CLASS[m.status]}`}>{translate({ id: `home.modules.status.${m.status}`, message: m.status })}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

    </Layout>
  );
}
