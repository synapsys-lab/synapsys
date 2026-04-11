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
            'guide/transport/shared-memory',
            'guide/transport/zmq',
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
