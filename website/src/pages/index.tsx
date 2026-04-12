import type { ReactElement } from 'react';
import Link from '@docusaurus/Link';
import Translate, { translate } from '@docusaurus/Translate';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import CodeBlock from '@theme/CodeBlock';
import {
  Zap,
  LayoutGrid,
  Calculator,
  Network,
  Share2,
  Cpu,
  type LucideIcon,
} from 'lucide-react';
import ControlSystemBackground from '../components/ControlSystemBackground';

const GITHUB = 'https://github.com/synapsys-lab/synapsys';

// ── Feature cards ─────────────────────────────────────────────────────────────
const FEATURES: { id: string; Icon: LucideIcon; title: string; desc: string; href: string }[] = [
  {
    id: 'matlab',
    Icon: Zap,
    title: translate({ id: 'home.feature.matlab.title',    message: 'MATLAB-Compatible API' }),
    desc:  translate({ id: 'home.feature.matlab.desc',     message: 'tf(), ss(), step(), bode(), feedback() — familiar syntax, pure Python. Zero MATLAB licence required.' }),
    href: '/docs/api/matlab-compat',
  },
  {
    id: 'lti',
    Icon: LayoutGrid,
    title: translate({ id: 'home.feature.lti.title',       message: 'Solid LTI Core' }),
    desc:  translate({ id: 'home.feature.lti.desc',        message: 'TransferFunction and StateSpace with full operator algebra, poles, zeros, stability analysis and ZOH discretisation.' }),
    href: '/docs/guide/core/transfer-function',
  },
  {
    id: 'algorithms',
    Icon: Calculator,
    title: translate({ id: 'home.feature.algorithms.title', message: 'Control Algorithms' }),
    desc:  translate({ id: 'home.feature.algorithms.desc',  message: 'Discrete PID with anti-windup and saturation. LQR via algebraic Riccati equation. Production-ready.' }),
    href: '/docs/guide/algorithms/pid',
  },
  {
    id: 'agents',
    Icon: Network,
    title: translate({ id: 'home.feature.agents.title',    message: 'Multi-Agent Simulation' }),
    desc:  translate({ id: 'home.feature.agents.desc',     message: 'PlantAgent and ControllerAgent with FIPA ACL messaging. Lock-step and wall-clock synchronisation.' }),
    href: '/docs/guide/agents/concepts',
  },
  {
    id: 'transport',
    Icon: Share2,
    title: translate({ id: 'home.feature.transport.title', message: 'Pluggable Transport' }),
    desc:  translate({ id: 'home.feature.transport.desc',  message: 'Zero-copy shared memory for single-host simulation. ZeroMQ PUB/SUB and REQ/REP for distributed setups.' }),
    href: '/docs/guide/transport/overview',
  },
  {
    id: 'hw',
    Icon: Cpu,
    title: translate({ id: 'home.feature.hw.title',        message: 'Hardware Abstraction' }),
    desc:  translate({ id: 'home.feature.hw.desc',         message: 'HardwareInterface enables seamless MIL → SIL → HIL transitions. MockHardwareInterface for in-process testing.' }),
    href: '/docs/guide/agents/hil-sil',
  },
];

// ── Stats ─────────────────────────────────────────────────────────────────────
const STATS = [
  { value: '74',    label: translate({ id: 'home.stat.tests',   message: 'Tests Passing' }) },
  { value: '86%',   label: translate({ id: 'home.stat.cov',     message: 'Coverage' }) },
  { value: '3.10+', label: translate({ id: 'home.stat.python',  message: 'Python' }) },
  { value: 'MIT',   label: translate({ id: 'home.stat.license', message: 'License' }) },
];

// ── How it works steps ────────────────────────────────────────────────────────
const STEPS = [
  {
    n: '01',
    title: translate({ id: 'home.step1.title', message: 'Install' }),
    desc:  translate({ id: 'home.step1.desc',  message: 'One pip command, no native dependencies.' }),
    code: 'pip install synapsys',
  },
  {
    n: '02',
    title: translate({ id: 'home.step2.title', message: 'Model Your System' }),
    desc:  translate({ id: 'home.step2.desc',  message: 'Define plants and controllers with the MATLAB-compatible API.' }),
    code: 'G = tf([1], [1, 2, 1])',
  },
  {
    n: '03',
    title: translate({ id: 'home.step3.title', message: 'Simulate & Deploy' }),
    desc:  translate({ id: 'home.step3.desc',  message: 'Run agents on shared memory or ZMQ. Scale from laptop to lab.' }),
    code: 'agent.start(blocking=False)',
  },
];

// ── Sub-components ────────────────────────────────────────────────────────────
function Feature({ Icon, title, desc, href }: { Icon: LucideIcon; title: string; desc: string; href: string }): ReactElement {
  return (
    <Link to={href} className="feature__card">
      <span className="feature__icon">
        <Icon size={24} strokeWidth={1.75} />
      </span>
      <h3 className="feature__title">{title}</h3>
      <p className="feature__desc">{desc}</p>
    </Link>
  );
}

function Step({
  n, title, desc, code, last,
}: {
  n: string; title: string; desc: string; code: string; last?: boolean;
}) {
  return (
    <div className="step__wrapper">
      <div className="step__item">
        <div className="step__number">{n}</div>
        <div className="step__body">
          <h3 className="step__title">{title}</h3>
          <p className="step__desc">{desc}</p>
          <code className="step__code">{code}</code>
        </div>
      </div>
      {!last && <div className="step__connector" aria-hidden="true">→</div>}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Home(): ReactElement {
  const { siteConfig } = useDocusaurusContext();

  return (
    <Layout
      title={siteConfig.title}
      description={translate({
        id: 'home.meta.description',
        message: 'Modern Python control systems framework with distributed multi-agent simulation',
      })}
    >
      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <header className="hero--synapsys">
        <div className="hero__inner">
          <div className="hero__badge-row">
            <span className="hero__badge">v0.1.0 Alpha</span>
            <span className="hero__badge hero__badge--neutral">Python 3.10+</span>
            <span className="hero__badge hero__badge--neutral">MIT</span>
          </div>

          <h1 className="hero__title--gradient">{siteConfig.title}</h1>

          <p className="hero__subtitle">
            <Translate id="home.hero.tagline">
              Modern Python control systems framework with distributed multi-agent simulation.
              MATLAB-compatible API, zero-copy shared memory, and a pluggable transport layer
              that scales from laptop to lab.
            </Translate>
          </p>

          <div className="hero__install">
            <code className="hero__install-cmd">pip install synapsys</code>
            <span className="hero__install-version">
              <Translate id="home.hero.latest">latest: 0.1.0</Translate>
            </span>
          </div>

          <div className="hero__buttons">
            <Link className="hero__cta-primary" to="/docs/getting-started/installation">
              <Translate id="home.hero.cta.start">Get Started →</Translate>
            </Link>
            <Link className="hero__cta-secondary" to={GITHUB}>
              GitHub
            </Link>
            <Link className="hero__cta-secondary" to="/docs/api/core">
              <Translate id="home.hero.cta.api">API Reference</Translate>
            </Link>
          </div>
        </div>
      </header>

      {/* ── Stats bar ─────────────────────────────────────────────────────── */}
      <div className="stats__bar">
        {STATS.map((s) => (
          <div key={s.label} className="stat__item">
            <span className="stat__value">{s.value}</span>
            <span className="stat__label">{s.label}</span>
          </div>
        ))}
      </div>

      {/* ── Live control system animation ─────────────────────────────────── */}
      <section className="diagram__section">
        <p className="diagram__label">
          <Translate id="home.diagram.label">
            Closed-loop control system — animated signal flow
          </Translate>
        </p>
        <ControlSystemBackground style={{ height: 260 }} />
      </section>

      {/* ── Feature cards ─────────────────────────────────────────────────── */}
      <section className="features__section">
        <h2 className="section__title">
          <Translate id="home.features.title">Everything you need</Translate>
        </h2>
        <p className="section__subtitle">
          <Translate id="home.features.subtitle">
            From LTI math to real-time distributed simulation in one library.
          </Translate>
        </p>
        <div className="features__grid">
          {FEATURES.map((f) => (
            <Feature key={f.id} Icon={f.Icon} title={f.title} desc={f.desc} href={f.href} />
          ))}
        </div>
      </section>

      {/* ── How it works ──────────────────────────────────────────────────── */}
      <section className="steps__section">
        <h2 className="section__title">
          <Translate id="home.steps.title">Up and running in 3 steps</Translate>
        </h2>
        <div className="steps__row">
          {STEPS.map((s, i) => (
            <Step key={s.n} {...s} last={i === STEPS.length - 1} />
          ))}
        </div>
      </section>

      {/* ── Code examples ─────────────────────────────────────────────────── */}
      <section className="code__section">
        <h2 className="section__title">
          <Translate id="home.code.title">See it in action</Translate>
        </h2>
        <div className="code__tabs-wrapper">
          <Tabs>
            <TabItem value="core" label={translate({ id: 'home.tab.core', message: 'Core Math' })}>
              <CodeBlock language="python" title="LTI systems · Bode · step response">
{`from synapsys.api import tf, step, bode, feedback, c2d

# Transfer function — MATLAB syntax
G = tf([1], [1, 2, 1])      # G(s) = 1 / (s² + 2s + 1)

# Closed-loop with negative feedback
T = feedback(G)              # T(s) = G / (1 + G)
t, y = step(T)               # step response

# Frequency response
w, mag, phase = bode(G)

# ZOH discretisation at 50 Hz
Gd = c2d(G, dt=0.02)`}
              </CodeBlock>
            </TabItem>

            <TabItem value="algorithms" label={translate({ id: 'home.tab.algorithms', message: 'Algorithms' })}>
              <CodeBlock language="python" title="Discrete PID · LQR">
{`from synapsys.algorithms import PID, lqr
import numpy as np

# Discrete PID with anti-windup and output saturation
pid = PID(Kp=3.0, Ki=0.5, Kd=0.1, dt=0.01,
          u_min=-10.0, u_max=10.0)
u = pid.compute(setpoint=5.0, measurement=y)

# LQR — solves the algebraic Riccati equation
A = np.array([[ 0., 1.], [-2., -3.]])
B = np.array([[0.], [1.]])
K, P = lqr(A, B, Q=np.eye(2), R=np.eye(1))`}
              </CodeBlock>
            </TabItem>

            <TabItem value="distributed" label={translate({ id: 'home.tab.distributed', message: 'Multi-Agent' })}>
              <CodeBlock language="python" title="PlantAgent + ControllerAgent on shared memory">
{`from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, ControllerAgent, SyncEngine, SyncMode
from synapsys.algorithms import PID
from synapsys.transport import SharedMemoryTransport
import numpy as np

plant_d = c2d(ss([[-1]], [[1]], [[1]], [[0]]), dt=0.01)

bus = SharedMemoryTransport("demo", {"y": 1, "u": 1}, create=True)
bus.write("y", np.zeros(1))
bus.write("u", np.zeros(1))

pid = PID(Kp=4.0, Ki=1.0, dt=0.01)
law = lambda y: np.array([pid.compute(setpoint=3.0, measurement=y[0])])

PlantAgent("plant", plant_d, bus, SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)).start(blocking=False)
ControllerAgent("ctrl", law, bus,  SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)).start(blocking=False)`}
              </CodeBlock>
            </TabItem>

            <TabItem value="hil" label={translate({ id: 'home.tab.hil', message: 'MIL → HIL' })}>
              <CodeBlock language="python" title="Swap transport — algorithm unchanged">
{`# MIL — everything in process memory
from synapsys.transport import SharedMemoryTransport
bus = SharedMemoryTransport("sim", channels, create=True)

# SIL — cross-process or cross-machine via ZMQ
from synapsys.transport import ZMQTransport
bus = ZMQTransport("tcp://localhost:5555", mode="pub")

# HIL — real hardware, same controller
from synapsys.agents import HardwareAgent
from synapsys.hw import MockHardwareInterface   # swap for your hardware driver

hw    = MockHardwareInterface(n_inputs=1, n_outputs=1, plant_fn=my_hw)
agent = HardwareAgent("hw", hw, bus, sync)

# ControllerAgent and PID/LQR stay exactly the same in all three modes`}
              </CodeBlock>
            </TabItem>
          </Tabs>
        </div>
      </section>

      {/* ── Bottom CTA ────────────────────────────────────────────────────── */}
      <section className="bottom-cta__section">
        <div className="bottom-cta__inner">
          <h2 className="bottom-cta__title">
            <Translate id="home.cta.title">Ready to control something real?</Translate>
          </h2>
          <p className="bottom-cta__subtitle">
            <Translate id="home.cta.subtitle">
              Start with the quickstart guide or dive straight into the API reference.
            </Translate>
          </p>
          <div className="hero__buttons">
            <Link className="hero__cta-primary" to="/docs/getting-started/installation">
              <Translate id="home.cta.start">Get Started →</Translate>
            </Link>
            <Link className="hero__cta-secondary" to={GITHUB}>
              View on GitHub
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  );
}
