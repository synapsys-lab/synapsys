import type { ReactElement } from 'react';
import Link from '@docusaurus/Link';
import Translate, { translate } from '@docusaurus/Translate';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Layout from '@theme/Layout';
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import CodeBlock from '@theme/CodeBlock';
import {
  BookOpen,
  Cpu,
  FlaskConical,
  LayoutList,
  GitBranch,
  ArrowRight,
  type LucideIcon,
} from 'lucide-react';

const GITHUB = 'https://github.com/synapsys-lab/synapsys';

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

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Home(): ReactElement {
  const { siteConfig } = useDocusaurusContext();
  const logoUrl = useBaseUrl('/img/logo.svg');

  return (
    <Layout
      title={siteConfig.title}
      description={translate({
        id: 'home.meta.description',
        message: 'Python control systems library — LTI models, PID, LQR and distributed multi-agent simulation',
      })}
    >

      {/* ── Header ────────────────────────────────────────────────────────── */}
      <header className="doc-header">
        <div className="doc-header__inner">
          <div className="doc-header__cols">

            {/* ── Logo column ── */}
            <div className="doc-header__logo-col">
              <img src={logoUrl} alt="Synapsys logo" className="doc-header__logo" />
            </div>

            {/* ── Content column ── */}
            <div className="doc-header__content-col">
              <div className="doc-header__meta">
                <span className="doc-badge">v0.1.0</span>
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

              <div className="doc-header__install">
                <code>pip install synapsys</code>
                <span className="doc-header__sep">or</span>
                <code>uv add synapsys</code>
              </div>

              <div className="doc-header__actions">
                <Link className="btn btn--primary" to="/docs/getting-started/installation">
                  <Translate id="home.header.cta.docs">Documentation</Translate>
                </Link>
                <Link className="btn btn--outline" to={GITHUB}>
                  <GitBranch size={15} /> GitHub
                </Link>
                <Link className="btn btn--outline" to="/docs/getting-started/quickstart">
                  <Translate id="home.header.cta.quickstart">Quickstart</Translate>
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
          </Tabs>
        </div>
      </section>

      {/* ── Module overview ────────────────────────────────���──────────────── */}
      <section className="content-section content-section--alt">
        <div className="content-section__inner">
          <h2 className="content-section__title">
            <Translate id="home.modules.title">Package Overview</Translate>
          </h2>
          <table className="module-table">
            <thead>
              <tr>
                <th>Package</th>
                <th>Contents</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {MODULES.map((m) => (
                <tr key={m.pkg}>
                  <td><code>{m.pkg}</code></td>
                  <td className="module-table__desc">{m.desc}</td>
                  <td><span className={`status-badge ${STATUS_CLASS[m.status]}`}>{m.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── MIL → HIL pipeline ────────────────────��───────────────────────── */}
      <section className="content-section">
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
              <span className="pipeline__name">Model-in-the-Loop</span>
              <span className="pipeline__detail">SharedMemoryTransport · PlantAgent</span>
            </div>
            <ArrowRight className="pipeline__arrow" size={18} />
            <div className="pipeline__stage">
              <span className="pipeline__label">SIL</span>
              <span className="pipeline__name">Software-in-the-Loop</span>
              <span className="pipeline__detail">ZMQTransport · separate process</span>
            </div>
            <ArrowRight className="pipeline__arrow" size={18} />
            <div className="pipeline__stage">
              <span className="pipeline__label">HIL</span>
              <span className="pipeline__name">Hardware-in-the-Loop</span>
              <span className="pipeline__detail">HardwareAgent · real device</span>
            </div>
          </div>
          <p className="pipeline__note">
            See the{' '}
            <Link to="/docs/guide/agents/hil-sil">HIL / SIL guide</Link>
            {' '}for a step-by-step migration example.
          </p>
        </div>
      </section>

    </Layout>
  );
}
