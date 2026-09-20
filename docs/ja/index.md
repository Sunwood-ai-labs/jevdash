---
layout: home

hero:
  name: "JevDash: System One"
  text: "自律型AI 2Dプラットフォーマー"
  tagline: "100% クリーンルーム・著作権フリー設計の TypeSafe Jev 向け 60 FPS ベンチマーク"
  image:
    src: /gameplay.gif
    alt: JevDash リアルタイム自律走行
  actions:
    - theme: brand
      text: クイックスタート
      link: /ja/guide/getting-started
    - theme: alt
      text: GitHub リポジトリ
      link: https://github.com/Sunwood-ai-labs/jevdash

features:
  - icon: 🛡️
    title: 100% クリーンルーム設計
    details: 既存の商用ゲームROMや著作権保護アセットを一切不使用。商用評価、OSSデモ、学術研究でも法的に安全です。
  - icon: ⚡
    title: TypeSafe Jev 実機連携（Vercel 無料枠対応）
    details: Vercel AI Gateway（typesafe-ai/jev）の無料枠（Hobby プラン）から即座に利用可能。Choice、Boolean、Score などの型安全プリミティブによる高速推論を実現。
  - icon: 🎥
    title: リアルタイム MP4 録画
    details: FFmpeg パイプラインを内蔵し、1280x720 60 FPS の高精細 H.264 ゲームプレイ動画を自動キャプチャ。
  - icon: 📊
    title: Apple HIG / Keynote 風 HUD
    details: リアルタイム確率バー、危険度メーター、推論レイテンシ計測、7x11 ASCII レーダーを備えた洗練されたHUDを搭載。
---

## 🎮 リアルタイム AI 自律走行デモ

<div style="text-align: center; margin: 1.5rem 0 2rem 0;">
  <img src="/gameplay.gif" alt="JevDash リアルタイム自律走行デモ" style="border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 100%;">
</div>

### リアルタイム・テレメトリと知覚
- **非同期意思決定パイプライン**: 60 FPS の物理ループを一切阻害せずに Jev モデルへサブフレーム推論をディスパッチ。
- **Keynote スタイル HUD**: Choice 確率分布バー、危険度スコア（1〜10）、推論レイテンシ、7×11 ASCII 空間レーダーをリアルタイム表示。
- **常時 MP4 録画**: 全走行フレームを 1280×720 60 FPS (H.264) の高画質動画として自動エンコード。
