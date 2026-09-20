# JevDash をはじめよう

**JevDash: System One** へようこそ。TypeSafe Jev モデルのリアルタイム物理制御性能を検証する高性能 2D プラットフォーマー・ベンチマークです。

---

## 必要な環境

- **Python**: 3.12 以降（3.13 推奨）
- **uv**: 高速 Python パッケージマネージャー（[インストール方法](https://docs.astral.sh/uv/)）
- **FFmpeg**: 任意（動画録画機能 `uv run jevdash play --record ...` を使用する場合のみ必要）

---

## インストール手順

リポジトリをクローンし、`uv` で依存関係を一括インストールします：

```bash
git clone https://github.com/Sunwood-ai-labs/jevdash.git
cd jevdash

# 仮想環境の構築と依存関係の同期
uv sync --extra dev
```

---

## ゲームの起動方法

### 1. 手動操作モード（人間プレイヤー）

キーボードでキャラクターを直接操作します。プレイ中に `Tab` キーを押すことで、いつでも AI 自動操縦へシームレスに切り替えられます。

```bash
uv run jevdash play --mode human
```

#### 操作一覧:
- **← / →**（または **A / D**）: 左右移動
- **Shift**（長押し）: ダッシュ（最高速度）
- **Space**（または **W / ↑**）: ジャンプ（長押しで跳躍力増加）
- **Tab**: **AI オートパイロット ⇄ 手動操作の即時切り替え**
- **R**: リスタート
- **Q / Esc**: ゲーム終了

### 2. シミュレーション AI モード（API キー不要）

内蔵の決定論的解析エンジン（MockAgent）による自動プレイを実行します：

```bash
uv run jevdash play --mode mock
```

### 3. Vercel AI Gateway 経由の実モデル連携モード

Vercel AI Gateway 上で動作する本物の **TypeSafe Jev**（`typesafe-ai/jev`）を用いて実行します：

1. `.env.example` をコピーして `.env` を作成します：
   ```bash
   cp .env.example .env
   ```
2. `.env` に Vercel AI Gateway の API キーを設定します：
   ```env
   AI_GATEWAY_API_KEY=vck_your_api_key_here
   ```
3. ゲームを起動します（MP4 録画オプション付き）：
   ```bash
   uv run jevdash play --mode live --record jevdash_live.mp4
   ```

---

## テストの実行

ユニットテストを実行して、動作を確認します：

```bash
uv run pytest -v
```
