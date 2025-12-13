# ActingDoll

MCPを使ってLLMにLive2Dを動かすための命令を生成してもらうツールです。

## 概要

ActingDollは、[Model Context Protocol (MCP)](https://modelcontextprotocol.io/)を利用して、LLM（大規模言語モデル）がLive2Dモデルを制御するためのサーバーです。Live2Dは「Live2D Cubism SDK」で起動したWebサーバーを使用します。

## 機能

- **パラメータ設定**: Live2Dモデルのパラメータ（顔の角度、目の開き具合、口の開き具合など）を設定
- **表情設定**: モデルの表情（happy, sad, angryなど）を切り替え
- **モーション再生**: 登録されたモーションを再生
- **モデル情報取得**: 利用可能なパラメータ、表情、モーションの一覧を取得
- **ポーズリセット**: モデルをデフォルトの状態に戻す
- **視線設定**: モデルの視線を設定

## インストール

```bash
pip install acting-doll
```

または、開発用にインストールする場合：

```bash
git clone https://github.com/CodeneAria/ActingDoll.git
cd ActingDoll
pip install -e ".[dev]"
```

## 使用方法

### Live2D Cubism SDK Webサーバーの準備

まず、Live2D Cubism SDKを使用してWebサーバーを起動してください。サーバーはデフォルトで `http://localhost:8080` で起動することを想定しています。

### MCP設定

お使いのMCPクライアント（Claude Desktop、VS Codeなど）の設定ファイルに以下を追加してください：

```json
{
  "mcpServers": {
    "acting-doll": {
      "command": "acting-doll",
      "env": {
        "LIVE2D_SERVER_URL": "http://localhost:8080"
      }
    }
  }
}
```

### 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|--------------|
| `LIVE2D_SERVER_URL` | Live2D Cubism SDK WebサーバーのURL | `http://localhost:8080` |

## MCP ツール一覧

### set_parameter

Live2Dモデルのパラメータを設定します。

**入力:**

- `parameter_id` (string): パラメータID（例: ParamAngleX, ParamEyeLOpen）
- `value` (number): 設定する値（角度は-30〜30、開閉は0〜1が一般的）

### set_expression

Live2Dモデルの表情を設定します。

**入力:**

- `expression_id` (string): 表情ID（例: happy, sad, angry）

### start_motion

Live2Dモデルのモーションを開始します。

**入力:**

- `group` (string): モーショングループ名（例: Idle, TapBody）
- `index` (integer): モーションのインデックス（0から開始）
- `priority` (integer, optional): モーション優先度（1=アイドル, 2=通常, 3=強制）

### get_model_info

現在のLive2Dモデルの情報を取得します。

### reset_pose

Live2Dモデルをデフォルトのポーズにリセットします。

### set_look_at

Live2Dモデルの視線を設定します。

**入力:**

- `x` (number): X座標（-1.0〜1.0、左から右）
- `y` (number): Y座標（-1.0〜1.0、下から上）

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。
