import { useRef, useEffect, useState, type ReactElement, type CSSProperties } from 'react';
import Link from '@docusaurus/Link';

type Status = 'Stable' | 'Functional' | 'Interface' | 'Planned';

interface Package {
  pkg: string;
  label: string;
  desc: string;
  classes: string[];
  status: Status;
  href: string;
  accent: string;
  delay: number;
}

const PACKAGES: Package[] = [
  {
    pkg: 'synapsys.api',
    label: 'MATLAB-Compatible API',
    desc: 'Familiar entry point — mirrors the MATLAB Control Toolbox interface.',
    classes: ['tf()', 'ss()', 'c2d()', 'feedback()', 'series()', 'parallel()', 'bode()', 'step()', 'lsim()'],
    status: 'Stable',
    href: '/docs/api/matlab-compat',
    accent: '#c8a870',
    delay: 0,
  },
  {
    pkg: 'synapsys.core',
    label: 'Core LTI Systems',
    desc: 'Mathematical backbone — transfer functions, state-space and MIMO matrices.',
    classes: ['TransferFunction', 'StateSpace', 'TransferFunctionMatrix', 'LTIModel'],
    status: 'Stable',
    href: '/docs/api/core',
    accent: '#c8a870',
    delay: 1,
  },
  {
    pkg: 'synapsys.algorithms',
    label: 'Control Algorithms',
    desc: 'Discrete PID with anti-windup and LQR via the Algebraic Riccati Equation.',
    classes: ['PID', 'lqr()'],
    status: 'Stable',
    href: '/docs/api/algorithms',
    accent: '#c8a870',
    delay: 2,
  },
  {
    pkg: 'synapsys.agents',
    label: 'Multi-Agent Simulation',
    desc: 'Lifecycle agents for real-time closed-loop simulation with lock-step or wall-clock sync.',
    classes: ['BaseAgent', 'PlantAgent', 'ControllerAgent', 'SyncEngine', 'SyncMode', 'ACLMessage'],
    status: 'Functional',
    href: '/docs/api/agents',
    accent: '#0d9488',
    delay: 3,
  },
  {
    pkg: 'synapsys.broker',
    label: 'Message Broker',
    desc: 'High-level pub/sub bus decoupled from the transport layer — shared memory or ZMQ backend.',
    classes: ['MessageBroker', 'Topic', 'SharedMemoryBackend', 'ZMQBrokerBackend'],
    status: 'Functional',
    href: '/docs/guide/transport/broker',
    accent: '#0d9488',
    delay: 4,
  },
  {
    pkg: 'synapsys.transport',
    label: 'Transport Layer',
    desc: 'Zero-copy IPC and networked PUB/SUB for distributed MIL → SIL → HIL workflows.',
    classes: ['SharedMemoryTransport', 'ZMQTransport', 'ZMQReqRepTransport', 'TransportStrategy'],
    status: 'Functional',
    href: '/docs/api/transport',
    accent: '#0d9488',
    delay: 5,
  },
  {
    pkg: 'synapsys.utils',
    label: 'Utilities',
    desc: 'Matrix builders and declarative state-equation DSL for clean model definitions.',
    classes: ['StateEquations', 'mat()', 'col()', 'row()'],
    status: 'Stable',
    href: '/docs/api/utils',
    accent: '#c8a870',
    delay: 6,
  },
  {
    pkg: 'synapsys.hw',
    label: 'Hardware Interface',
    desc: 'Abstract interface for FPGA, FPAA and microcontroller backends — planned for v0.5.',
    classes: ['HardwareInterface', 'MockHardwareInterface'],
    status: 'Interface',
    href: '/docs/api/hw',
    accent: '#d97706',
    delay: 7,
  },
  {
    pkg: 'synapsys.observers',
    label: 'State Observers',
    desc: 'Kalman filter and Luenberger observer for state estimation — planned for v0.3.',
    classes: ['KalmanFilter', 'LuenbergerObserver'],
    status: 'Planned',
    href: '/docs/roadmap',
    accent: '#6b7280',
    delay: 8,
  },
];

const STATUS_COLOR: Record<Status, string> = {
  Stable:     '#16a34a',
  Functional: '#0d9488',
  Interface:  '#d97706',
  Planned:    '#6b7280',
};

const STATUS_DOT: Record<Status, string> = {
  Stable:     'lib-map__dot--stable',
  Functional: 'lib-map__dot--functional',
  Interface:  'lib-map__dot--interface',
  Planned:    'lib-map__dot--planned',
};

function PackageCard({ pkg, visible }: { pkg: Package; visible: boolean }): ReactElement {
  return (
    <Link
      to={pkg.href}
      className={`lib-map__card ${visible ? 'lib-map__card--visible' : ''}`}
      style={{
        '--lm-delay': `${pkg.delay * 90}ms`,
        '--lm-accent': pkg.accent,
      } as CSSProperties}
    >
      <div className="lib-map__card-top">
        <span className="lib-map__pkg">{pkg.pkg}</span>
        <span className="lib-map__status" style={{ color: STATUS_COLOR[pkg.status] }}>
          <span className={`lib-map__dot ${STATUS_DOT[pkg.status]}`} />
          {pkg.status}
        </span>
      </div>

      <p className="lib-map__label">{pkg.label}</p>
      <p className="lib-map__desc">{pkg.desc}</p>

      <div className="lib-map__pills">
        {pkg.classes.map((cls) => (
          <span key={cls} className="lib-map__pill">{cls}</span>
        ))}
      </div>
    </Link>
  );
}

export default function LibraryMap(): ReactElement {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) { setVisible(true); obs.disconnect(); }
      },
      { threshold: 0.1 },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <div ref={ref} className="lib-map">
      {PACKAGES.map((pkg) => (
        <PackageCard key={pkg.pkg} pkg={pkg} visible={visible} />
      ))}
    </div>
  );
}
