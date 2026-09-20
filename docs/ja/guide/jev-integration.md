# Jev AI 意思決定連携

**JevDash** は、**TypeSafe Jev**（`typesafe-ai/jev`）の実時間物理応答速度、空間推論能力、意思決定レイテンシを評価・実証するために構築されています。

---

## 1. TypeSafe Jev の概要

TypeSafe Jev は、厳格なスキーマ準拠、超低レイテンシ推論、決定論的なツール／アクション生成に特化した推論モデルアーキテクチャです。JevDash において Jev は、リアルタイムに変化する物理プラットフォーム環境を自律走破する「運動中枢エージェント」として機能します。

---

## 2. Vercel AI Gateway 連携

JevDash は、OpenAI 互換のインターフェースを通じて **Vercel AI Gateway** 経由で Jev と通信します：

- **Base URL**: `https://ai-gateway.vercel.sh/v1`
- **モデル名**: `typesafe-ai/jev`
- **認証**: Bearer トークン（`AI_GATEWAY_API_KEY`）

### 環境変数設定（.env）

```env
AI_GATEWAY_API_KEY=vck_your_secret_token_here
AI_GATEWAY_BASE_URL=https://ai-gateway.vercel.sh/v1
JEV_MODEL_NAME=typesafe-ai/jev
```

---

## 3. 意思決定パイプライン

各観測フレームにおいて、以下のフローで制御が実行されます：

1. **状態のシリアライズ**: 座標や速度などの空間情報をコンパクトなプロンプトへ変換。
2. **運動方程式ヒントの提示**: 落とし穴や壁までの到達予測時間（Time-to-Impact: TTI）を事前計算してプロンプトへ付与：
   ```text
   Current Velocity: vx=6.2 px/frame
   Next Hazard: Pit at distance 95.0 px (Est. 15 frames to edge)
   Jump Range at current speed: 140.0 px
   ```
3. **構造化レスポンスの生成**: Jev が即時アクションを含む JSON を返却：
   ```json
   {
     "action": "JUMP_AND_SPRINT",
     "reasoning": "前方 95px に幅 110px の穴を確認。ダッシュ速度を維持して 140px のジャンプ軌道で飛び越えます。"
   }
   ```
4. **アクチュエータキューへの格納**: 内部ループが指示を受け取り、60 FPS の物理ステップへ展開して反映。

---

## 4. フォールバック：決定論的 MockAgent

オフライン環境での開発や CI（継続的インテグレーション）での自動テスト向けに、レイテンシゼロの解析的 **MockAgent** が標準搭載されています：

```bash
uv run jevdash play --mode mock
```

MockAgent は幾何学レイキャストと放物線軌道予測により、100% の再現性でステージをクリアします。

---

## 5. テレメトリとベンチマーク指標

JevDash はプレイ中のエージェント挙動をリアルタイム計測します：
- **意思決定頻度（Decision Frequency）**: 1 秒あたりのエージェント推論回数（Hz）
- **推論往復時間（RTT Latency）**: ネットワーク往復遅延とトークン処理時間
- **平均走破速度（Traversal Velocity）**: ステージ通過時の水平移動速度
- **ステージクリア所要時間（Clear Time）**: スポーンからゴールポータル到達までの秒数
