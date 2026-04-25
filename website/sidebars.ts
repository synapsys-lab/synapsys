import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    {
      type: 'doc',
      id: 'intro',
      label: 'Introduction',
    },
    {
      type: 'category',
      label: 'Getting Started',
      items: [
        'getting-started/installation',
        'getting-started/quickstart',
      ],
    },
    {
      type: 'doc',
      id: 'architecture',
      label: 'Architecture',
    },
    {
      type: 'category',
      label: 'User Guide',
      items: [
        {
          type: 'category',
          label: 'Core — LTI Systems',
          items: [
            'guide/core/transfer-function',
            'guide/core/state-space',
            'guide/core/discrete',
          ],
        },
        {
          type: 'category',
          label: 'Algorithms',
          items: [
            'guide/algorithms/pid',
            'guide/algorithms/lqr',
          ],
        },
        {
          type: 'category',
          label: 'Multi-Agent Simulation',
          items: [
            'guide/agents/concepts',
            'guide/agents/plant-agent',
            'guide/agents/controller-agent',
            'guide/agents/hil-sil',
            'guide/agents/digital-twins',
          ],
        },
        {
          type: 'category',
          label: 'Transport Layer',
          items: [
            'guide/transport/overview',
            'guide/transport/broker',
            'guide/transport/shared-memory',
            'guide/transport/zmq',
          ],
        },
        {
          type: 'category',
          label: 'Utilities',
          items: [
            'guide/utils/matrix-builders',
          ],
        },
        {
          type: 'category',
          label: 'Simulators',
          items: [
            'guide/simulators/simulators-overview',
            'guide/simulators/simulators-msd',
            'guide/simulators/simulators-inverted-pendulum',
            'guide/simulators/simulators-cartpole',
          ],
        },
        {
          type: 'category',
          label: 'Visualization',
          items: [
            'guide/viz/viz-overview',
            'guide/viz/simview',
            'guide/viz/custom-controller',
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'Examples',
      items: [
        'examples/examples-index',
        {
          type: 'category',
          label: 'Basic',
          items: ['examples/basic/step-response'],
        },
        {
          type: 'category',
          label: 'Advanced',
          items: [
            'examples/advanced/custom-signals',
            'examples/advanced/sil-ai-controller',
            'examples/advanced/realtime-scope',
            'examples/advanced/realtime-oscilloscope',
            'examples/advanced/digital-twin',
            'examples/advanced/quadcopter-mimo',
          ],
        },
        {
          type: 'category',
          label: 'Distributed',
          items: [
            'examples/distributed/shared-memory-example',
            'examples/distributed/zmq-example',
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/matlab-compat',
        'api/core',
        'api/algorithms',
        'api/agents',
        'api/transport',
        'api/hw',
        'api/utils',
        'api/viz',
      ],
    },
    {
      type: 'doc',
      id: 'roadmap',
      label: 'Roadmap',
    },
  ],
};

export default sidebars;
