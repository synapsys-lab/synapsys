import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import { themes as prismThemes } from 'prism-react-renderer';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

const GITHUB = 'https://github.com/synapsys-lab/synapsys';

const config: Config = {
  title: 'Synapsys',
  tagline: 'Modern Python control systems framework with distributed multi-agent simulation',
  favicon: 'img/favicon.ico',

  url: 'https://synapsys-lab.github.io',
  baseUrl: '/synapsys/',

  organizationName: 'synapsys-lab',
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

  plugins: [
    'docusaurus-plugin-image-zoom',
    [
      '@easyops-cn/docusaurus-search-local',
      {
        hashed: true,
        language: ['en', 'pt'],
        indexBlog: true,
        indexDocs: true,
        indexPages: true,
        docsRouteBasePath: '/docs',
      },
    ],
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: `${GITHUB}/tree/main/website/`,
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
        },
        blog: {
          blogTitle: 'Synapsys Blog',
          blogDescription:
            'Tutorials, case studies and research insights for control systems engineers and researchers.',
          blogSidebarTitle: 'Recent posts',
          blogSidebarCount: 12,
          postsPerPage: 6,
          showReadingTime: true,
          remarkPlugins: [remarkMath],
          rehypePlugins: [rehypeKatex],
          feedOptions: {
            type: ['rss', 'atom'],
            title: 'Synapsys Blog',
            description:
              'Tutorials, case studies and research insights from the Synapsys control systems framework.',
            copyright: `Copyright © ${new Date().getFullYear()} Synapsys Contributors`,
            language: 'en',
          },
        },
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
    image: 'img/logo.svg',
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: false,
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: 'Synapsys',
      logo: { alt: 'Synapsys Logo', src: 'img/logo_light.svg', srcDark: 'img/logo_dark.svg' },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        { to: '/docs/api/core',  label: 'API',     position: 'left' },
        { to: '/docs/roadmap',   label: 'Roadmap', position: 'left' },
        { to: '/blog',           label: 'Blog',    position: 'left' },
        { type: 'docsVersionDropdown', position: 'right' },
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
            { label: 'Blog',      to: '/blog' },
            { label: 'Roadmap',   to: '/docs/roadmap' },
            { label: 'PyPI',      href: 'https://pypi.org/project/synapsys/' },
            { label: 'Changelog', href: `${GITHUB}/blob/main/CHANGELOG.md` },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Synapsys Contributors. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.vsDark,
      additionalLanguages: ['python', 'bash', 'yaml', 'toml'],
    },
    mermaid: {
      theme: { light: 'neutral', dark: 'dark' },
    },
    zoom: {
      selector: '.markdown img, .ai-showcase__img',
      background: {
        light: 'rgba(240, 244, 248, 0.92)',
        dark:  'rgba(15, 23, 42, 0.95)',
      },
      config: {
        margin: 24,
        scrollOffset: 0,
      },
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
