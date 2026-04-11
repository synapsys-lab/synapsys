import Link from '@docusaurus/Link';
import Translate, { translate } from '@docusaurus/Translate';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import CodeBlock from '@theme/CodeBlock';
import ControlSystemBackground from '../components/ControlSystemBackground';

const FEATURES = [
  {
    id: 'matlab',
    title: translate({ id: 'home.feature.matlab.title', message: 'MATLAB-Compatible API' }),
    desc:  translate({ id: 'home.feature.matlab.desc',  message: 'tf(), ss(), step(), bode(), feedback() — same syntax you already know, pure Python.' }),
  },
  {
    id: 'latency',
    title: translate({ id: 'home.feature.latency.title', message: 'Ultra-Low-Latency Transport' }),
    desc:  translate({ id: 'home.feature.latency.desc',  message: 'Zero-copy shared memory and ZeroMQ for sub-millisecond inter-process communication.' }),
  },
  {
    id: 'agents',
    title: translate({ id: 'home.feature.agents.title', message: 'Multi-Agent Simulation' }),
    desc:  translate({ id: 'home.feature.agents.desc',  message: 'PlantAgent and ControllerAgent with FIPA ACL messaging and lock-step / wall-clock sync.' }),
  },
  {
    id: 'lti',
    title: translate({ id: 'home.feature.lti.title', message: 'Solid LTI Core' }),
    desc:  translate({ id: 'home.feature.lti.desc',  message: 'TransferFunction and StateSpace with full operator overloading, poles, zeros, and stability.' }),
  },
  {
    id: 'algorithms',
    title: translate({ id: 'home.feature.algorithms.title', message: 'Algorithms' }),
    desc:  translate({ id: 'home.feature.algorithms.desc',  message: 'Discrete PID with anti-windup and LQR via algebraic Riccati equation — production-ready.' }),
  },
  {
    id: 'hw',
    title: translate({ id: 'home.feature.hw.title', message: 'Hardware Abstraction' }),
    desc:  translate({ id: 'home.feature.hw.desc',  message: 'Pluggable HardwareInterface for FPGA, FPAAs, and microcontrollers (planned).' }),
  },
];

function Feature({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="feature__card">
      <h3 className="feature__title">{title}</h3>
      <p className="feature__desc">{desc}</p>
    </div>
  );
}

export default function Home(): JSX.Element {
  const { siteConfig } = useDocusaurusContext();

  return (
    <Layout
      title={siteConfig.title}
      description={translate({
        id: 'home.meta.description',
        message: 'Modern Python control systems framework with distributed multi-agent simulation',
      })}
    >
      {/* Hero */}
      <header className="hero--synapsys">
        <h1 className="hero__title--gradient">{siteConfig.title}</h1>
        <p className="hero__subtitle">
          <Translate id="home.hero.tagline">
            Modern Python control systems framework with distributed multi-agent simulation
          </Translate>
        </p>
        <div className="hero__buttons">
          <Link className="hero__cta-primary" to="/docs/getting-started/installation">
            <Translate id="home.hero.cta.start">Get Started →</Translate>
          </Link>
          <Link className="hero__cta-secondary" to="https://github.com/synapsys/synapsys">
            GitHub
          </Link>
        </div>
      </header>

      {/* Control system diagram */}
      <section className="diagram__section">
        <ControlSystemBackground style={{ height: 280 }} />
      </section>

      {/* Feature cards */}
      <section className="features__section">
        <div className="features__grid">
          {FEATURES.map((f) => (
            <Feature key={f.id} title={f.title} desc={f.desc} />
          ))}
        </div>
      </section>

      {/* Code examples */}
      <section className="features__code-section">
        <Tabs>
          <TabItem
            value="core"
            label={translate({ id: 'home.tab.core', message: 'Core Math' })}
          >
            <CodeBlock language="python">
              {`from synapsys.api import tf, ss, step, bode, feedback, c2d

# Transfer function — same syntax as MATLAB
G = tf([1], [1, 2, 1])        # G(s) = 1 / (s² + 2s + 1)

# Block algebra
T = feedback(G)                # T = G / (1 + G)
t, y = step(T)                 # step response
w, mag, ph = bode(G)           # Bode diagram

# ZOH discretisation
Gd = c2d(G, dt=0.05)`}
            </CodeBlock>
          </TabItem>
          <TabItem
            value="algorithms"
            label={translate({ id: 'home.tab.algorithms', message: 'Algorithms' })}
          >
            <CodeBlock language="python">
              {`from synapsys.algorithms import PID, lqr

# Discrete PID with anti-windup
pid = PID(Kp=3.0, Ki=0.5, Kd=0.1, dt=0.01,
          u_min=-10.0, u_max=10.0)
u = pid.compute(setpoint=5.0, measurement=y)

# LQR — solves the algebraic Riccati equation
K, P = lqr(A, B, Q, R)`}
            </CodeBlock>
          </TabItem>
          <TabItem
            value="distributed"
            label={translate({ id: 'home.tab.distributed', message: 'Distributed Simulation' })}
          >
            <CodeBlock language="python">
              {`from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, SyncEngine
from synapsys.transport import SharedMemoryTransport

# Discretise the plant
plant_d = c2d(ss([[-1]], [[1]], [[1]], [[0]]), dt=0.01)

# Shared memory bus — zero-copy IPC
bus = SharedMemoryTransport("ctrl_bus", {"y": 1, "u": 1}, create=True)

agent = PlantAgent("plant", plant_d, bus, SyncEngine())
agent.start()   # non-blocking background thread`}
            </CodeBlock>
          </TabItem>
        </Tabs>
      </section>
    </Layout>
  );
}
