import type { ReactElement } from 'react';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Translate, { translate } from '@docusaurus/Translate';

interface SimulatorCard {
  id:     string;
  name:   string;
  gif:    string;
  state:  string;
  desc:   string;
  code:   string;
  href:   string;
}

const SIMULATORS: SimulatorCard[] = [
  {
    id:    'cartpole',
    name:  'Cart-Pole',
    gif:   '/img/simview/cartpole.gif',
    state: 'x = [x, ẋ, θ, θ̇]',
    desc:  'Inverted pendulum on a cart. 4 states, unstable — the classic benchmark for LQR and RL.',
    code:  'CartPoleView().run()',
    href:  '/docs/guide/viz/simview',
  },
  {
    id:    'pendulum',
    name:  'Inverted Pendulum',
    gif:   '/img/simview/pendulum.gif',
    state: 'x = [θ, θ̇]',
    desc:  'Single-link pendulum on a fixed base. The simplest unstable system for testing any controller.',
    code:  'PendulumView().run()',
    href:  '/docs/guide/viz/simview',
  },
  {
    id:    'msd',
    name:  'Mass-Spring-Damper',
    gif:   '/img/simview/msd.gif',
    state: 'x = [q, q̇]',
    desc:  'Mass-spring-damper with setpoint tracking. LQR with position feed-forward.',
    code:  'MassSpringDamperView().run()',
    href:  '/docs/guide/viz/simview',
  },
];

function SimCard({ id, name, gif, state, desc, code, href }: SimulatorCard): ReactElement {
  return (
    <div className="sim-card">
      <div className="sim-card__media">
        <img
          src={useBaseUrl(gif)}
          alt={translate({ id: `home.sims.${id}.alt`, message: `${name} 3D simulation` })}
          className="sim-card__gif"
          loading="lazy"
        />
      </div>
      <div className="sim-card__body">
        <div className="sim-card__header">
          <span className="sim-card__name">
            {translate({ id: `home.sims.${id}.name`, message: name })}
          </span>
          <span className="sim-card__state"><code>{state}</code></span>
        </div>
        <p className="sim-card__desc">
          {translate({ id: `home.sims.${id}.desc`, message: desc })}
        </p>
        <div className="sim-card__footer">
          <code className="sim-card__code">{code}</code>
          <Link to={href} className="sim-card__link">
            <Translate id="home.sims.docs_link">Docs →</Translate>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function SimulatorsShowcase(): ReactElement {
  return (
    <div className="sim-showcase">
      <div className="sim-showcase__grid">
        {SIMULATORS.map((s) => (
          <SimCard key={s.id} {...s} />
        ))}
      </div>

      <p className="sim-showcase__note">
        <Translate id="home.sims.note.prefix">
          Pass any callable as a controller — LQR, PID, neural network or RL agent:
        </Translate>
        {' '}
        <code>CartPoleView(controller=my_model).run()</code>
        {'  ·  '}
        <Link to="/docs/guide/viz/custom-controller">
          <Translate id="home.sims.note.link">See examples →</Translate>
        </Link>
      </p>
    </div>
  );
}
