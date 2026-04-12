import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import { themes as prismThemes } from 'prism-react-renderer';

const GITHUB = 'https://github.com/Oseiasdfarias/synapsys';

const config: Config = {
  title: 'Synapsys',
  tagline: 'Modern Python control systems framework with distributed multi-agent simulation',
  favicon: 'img/favicon.ico',

  url: 'https://oseiasdfarias.github.io',
  baseUrl: '/synapsys/',

  organizationName: 'Oseiasdfarias',
  projectName: 'synapsys',
  trailingSlash: false,

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'pt'],
    localeConfigs: {
      en: { label: 'English',         direction: 'ltr', htmlLang: 'en-US' },
      pt: { label: 'Português (BR)',   direction: 'ltr', htmlLang: 'pt-BR' },
    },
  },

  markdown: { mermaid: true },
  themes: ['@docusaurus/theme-mermaid'],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: `${GITHUB}/tree/main/website/`,
          remarkPlugins: [require('remark-math')],
          rehypePlugins: [require('rehype-katex')],
        },
        blog: false,
        theme: { customCss: './src/css/custom.css' },
      } satisfies Preset.Options,
    ],
  ],

  stylesheets: [
    {
      href: 'https://cdn.jsdelivr.net/npm/katex@0.13.24/dist/katex.min.css',
      type: 'text/css',
      integrity: 'sha384-odtC+0UGzzFL/6PNoE8rX/SPcQDXBJ+uRepguP4QkPCm2LBxH3FA3y+fKSiJ+AmM',
      crossorigin: 'anonymous',
    },
  ],

  themeConfig: {
    image: 'img/synapsys-social-card.png',
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Synapsys',
      logo: { alt: 'Synapsys Logo', src: 'img/logo.png' },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        { to: '/docs/api/core',  label: 'API',     position: 'left' },
        { to: '/docs/roadmap',   label: 'Roadmap', position: 'left' },
        { type: 'localeDropdown', position: 'right' },
        { href: GITHUB, label: 'GitHub', position: 'right' },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            { label: 'Getting Started', to: '/docs/getting-started/installation' },
            { label: 'Architecture',    to: '/docs/architecture' },
            { label: 'API Reference',   to: '/docs/api/core' },
          ],
        },
        {
          title: 'Community',
          items: [
            { label: 'GitHub',  href: GITHUB },
            { label: 'Issues',  href: `${GITHUB}/issues` },
            { label: 'Releases', href: `${GITHUB}/releases` },
          ],
        },
        {
          title: 'More',
          items: [
            { label: 'Roadmap', to: '/docs/roadmap' },
            { label: 'PyPI',    href: 'https://pypi.org/project/synapsys/' },
            { label: 'Changelog', href: `${GITHUB}/blob/main/CHANGELOG.md` },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Synapsys Contributors. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash', 'yaml', 'toml'],
    },
    mermaid: {
      theme: { light: 'neutral', dark: 'dark' },
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
