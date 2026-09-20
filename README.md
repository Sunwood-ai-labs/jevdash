# JevDash: System One 🎮 (Autonomous AI Benchmark)

**100% クリーンルーム・著作権フリー**の Jev AI リアルタイム意思決定ベンチマーク用 2D 横スクロールアクションゲーム。

任天堂のROMバイナリに依存する `gym-super-mario-bros` 等の著作権リスクを完全に排除し、企業・研究・オープンソースコミュニティで誰でも安全・合法にデモや技術検証ができるようにゼロから設計・実装されています。

---

![JevDash Stage Clear](assets/stage_clear.png)

> **JevDash: System One** is a 100% clean-room, copyright-free 2D side-scrolling platformer designed specifically for benchmarking and testing **TypeSafe AI's Jev** model in real-time control scenarios at 60 FPS. Completely eliminates all copyright and ROM risks associated with commercial games like `gym-super-mario-bros`.

---

## 🌟 特徴

1. **完全著作権フリー（Clean-Room Architecture）**:
   - 独自の物理エンジン、ネオン・サイバーミニマルなプログラマティック描画、オリジナルステージ設計。商用ゲームROMや外部画像アセットを一切必要としません。
2. **本物の Jev 実機推論（Vercel AI Gateway 連携）対応**:
   - Vercel AI Gateway 経由で本物の Jev モデル（`typesafe-ai/jev`）に直結し、リアルタイムに自律走行を制御。
3. **常時 MP4 動画キャプチャ機能（FFmpeg 統合）**:
   - ゲームプレイ中の 1280x720 60FPS 画面をリアルタイムに H.264 MP4 動画として自動エンコード・保存。
4. **APIキー不要の超高速 Mock AI も標準内蔵**:
   - API キーがなくても、組み込みの決定エンジンにより、Jev 同様の確率分布バーチャートと 100% ステージクリアの自律プレイを即座に体験可能。
5. **Apple HIG / Keynote スタイルのリアルタイム HUD**:
   - 画面右側に Jev の思考確率分布（Choice）、危険度メーター（Danger Score 1〜10）、推論レイテンシ（ms）、局所レーダー（ASCII）を美しく同時描画。
6. **人間プレイ ＆ ヘッドレスベンチマーク両対応**:
   - 手動キーボード操作（WASD/矢印キー）と自律AIのワンタッチ切替（Tabキー）。

---

## 🏗️ アーキテクチャ

```text
┌─────────────────────────────────────────────────────────────┐
│                   Pygame 2D Engine (60 FPS)                 │
│        プレイヤー・敵・地形衝突・コヨーテタイム物理演算     │
└──────────────────────────────┬──────────────────────────────┘
                               │ 毎 8 フレーム (約 133ms 周期)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Telemetry Extractor (Pydantic)              │
│       マリオの位置、速度、敵との衝突予測時間、穴・壁距離    │
└──────────────────────────────┬──────────────────────────────┘
                               │ 構造化 JSON (JevObservation)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               Decision Layer (Jev / Mock Jev)               │
│   ・Choice  : 7 つの行動マクロから確率選択                  │
│   ・Boolean : 緊急ジャンプの必要性を真偽判定                │
│   ・Score   : 直前の危険度を 1〜10 採点 (50ms 以下)         │
└──────────────────────────────┬──────────────────────────────┘
                               │ アクション実行 (right_run_jump 等)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│            HUD Dashboard (Keynote Style Live View)          │
│       確率分布バーチャート、レイテンシ、危険度メーター描画  │
└─────────────────────────────────────────────────────────────┘
```

![JevDash Split-Screen Gameplay](assets/gameplay_screenshot.png)

---

## 📦 セットアップ（uv を使用）

本プロジェクトは高速パッケージマネージャ `uv` で管理されています。

```powershell
git clone https://github.com/Sunwood-ai-labs/jevdash.git
cd jevdash

# 依存関係の同期（仮想環境自動作成）
uv sync --extra dev
```

---

## 🚀 使い方・コマンド

### 1. 本物の Jev でプレイ ＆ MP4 動画自動録画
Vercel AI Gateway 経由で本物の Jev（`typesafe-ai/jev`）に操作させ、MP4 動画を出力します。
```powershell
uv run jevdash play --mode live --record jevdash_live.mp4
```

### 2. 人間が手動操作でプレイ ＆ 録画
手動でアクションゲームを遊びながら、プレイ動画を記録します。
```powershell
uv run jevdash play --mode human --record jevdash_human.mp4
```
* **操作キー**:
  * `左右矢印` または `A/D`: 移動
  * `Shift`: ダッシュ（Run）
  * `Space` または `上矢印` / `W`: ジャンプ
  * `Tab`: **AI 自律プレイ ⇄ 手動人間プレイの即時切替**
  * `R`: ステージのリスタート
  * `Q` または `Esc`: ゲーム終了

### 3. 超高速 Mock AI による自律走行（100%クリア検証）
```powershell
uv run jevdash play --mode mock
```

### 4. 構造化 JSON テレメトリの確認（APIキー不要）
```powershell
uv run jevdash state-demo
```

### 5. 高速ヘッドレスベンチマーク
```powershell
uv run jevdash benchmark --episodes 5
```

---

## 🧪 テストの実行

```powershell
uv run pytest -v
```
物理演算、接地・コヨーテタイム、テレメトリ抽出、Vercel AI Gateway 接続、MP4 レコーダーのユニットテスト（全12件）が実行されます。

---

## 📄 ライセンス
MIT License - 商用・非商用問わず完全自由にご利用いただけます。
