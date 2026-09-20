import { defineConfig } from 'vitepress';

export default defineConfig({
  title: 'JevDash: System One',
  description: '100% Clean-Room 2D Autonomous AI Platformer Benchmark (60 FPS)',
  base: '/jevdash/',
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/jevdash/icon.svg' }],
    ['meta', { name: 'theme-color', content: '#38bdf8' }],
  ],

  locales: {
    root: {
      label: 'English',
      lang: 'en',
      themeConfig: {
        nav: [
          { text: 'Guide', link: '/guide/getting-started' },
          { text: 'Architecture', link: '/guide/architecture' },
          { text: 'Jev Integration', link: '/guide/jev-integration' },
        ],
        sidebar: [
          {
            text: 'Introduction',
            items: [
              { text: 'Getting Started', link: '/guide/getting-started' },
              { text: 'Architecture', link: '/guide/architecture' },
              { text: 'Jev AI Integration', link: '/guide/jev-integration' },
            ],
          },
        ],
        footer: {
          message: 'Released under the MIT License.',
          copyright: 'Copyright © 2026 Sunwood AI Labs',
        },
      },
    },
    ja: {
      label: '日本語',
      lang: 'ja',
      link: '/ja/',
      themeConfig: {
        nav: [
          { text: 'ガイド', link: '/ja/guide/getting-started' },
          { text: 'アーキテクチャ', link: '/ja/guide/architecture' },
          { text: 'Jev 連携', link: '/ja/guide/jev-integration' },
        ],
        sidebar: [
          {
            text: 'はじめに',
            items: [
              { text: 'クイックスタート', link: '/ja/guide/getting-started' },
              { text: 'アーキテクチャ設計', link: '/ja/guide/architecture' },
              { text: 'Jev AI 意思決定連携', link: '/ja/guide/jev-integration' },
            ],
          },
        ],
        footer: {
          message: 'MIT ライセンスの下で公開されています。',
          copyright: 'Copyright © 2026 Sunwood AI Labs',
        },
      },
    },
  },

  themeConfig: {
    logo: '/icon.svg',
    socialLinks: [
      { icon: 'github', link: 'https://github.com/Sunwood-ai-labs/jevdash' },
    ],
  },
});
