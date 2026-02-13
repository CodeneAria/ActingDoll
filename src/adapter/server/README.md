# Acting Doll Server

WebSocketとMCPプロトコルの両方をサポートする、Live2Dモデル制御用の統合サーバーです。

## 概要

このパッケージは、Live2DクライアントとのWebSocket通信と、LLM（Claude Desktop等）からのMCP経由制御の両方を1つのサーバーで実現します。

## 機能

- **WebSocketサーバー**: Live2Dクライアントとのリアルタイム通信
- **MCPサーバー**: LLMからのHTTP SSE (Server-Sent Events) 経由制御
- **統合モード**: WebSocketとMCPを同時実行
- **モデル管理**: Live2Dモデルの情報取得、パラメータ・表情・モーション制御
- **クライアント管理**: 接続中のクライアント一覧と状態監視

## インストール

### PyPIから（将来）

```bash
pip install acting-doll-server
```

### ローカルから

```bash
# 基本インストール（WebSocketのみ）
pip install .

# MCP機能も含める
pip install ".[mcp]"

# 開発用（テストツール含む）
pip install ".[dev]"

# すべて
pip install ".[all]"
```

### 開発モード

```bash
pip install -e ".[all]"
```

## 使い方

### コマンドラインインターフェース

インストール後、`acting-doll-server` コマンドが利用可能になります：

```bash
# WebSocketサーバーのみ（デフォルト）
acting-doll-server --mode websocket --port 8766 --disable-auth

# MCPサーバーのみ
acting-doll-server --mode mcp --model-dir /path/to/models

# 両方同時実行（推奨）
acting-doll-server --mode both --port 8766 --disable-auth
```

### モード説明

#### 1. WebSocketモード（`--mode websocket`）

Live2DクライアントとのWebSocket通信のみを行います。

```bash
acting-doll-server --mode websocket --port 8766 --host localhost --disable-auth
```

- Live2Dクライアントは `ws://localhost:8766` に接続
- コンソールから対話的にコマンド実行可能（`--no-console`で無効化）

#### 2. MCPモード（`--mode mcp`）

LLMからのHTTP SSE経由制御のみを行います。

```bash
acting-doll-server --mode mcp --model-dir src/Cubism/Resources --mcp-port 3001
```

- Claude Desktop等のMCPクライアントから使用
- HTTP SSE経由で通信（デフォルトポート: 3001、エンドポイント: `/sse`）

#### 3. 両方モード（`--mode both`）

WebSocketとMCPを同時実行します。

```bash
acting-doll-server --mode both --port 8766 --mcp-port 3001 --disable-auth
```

- WebSocket: `ws://localhost:8766`
- MCP: HTTP SSE経由（ポート: 3001、エンドポイント: `/sse`）
- 1つのプロセスで両方を処理

### コマンドライン引数

```
--mode {websocket,mcp,both}  動作モード（デフォルト: websocket）
--model-dir PATH             モデルディレクトリのパス
--host HOST                  WebSocketおよびMCPサーバーのホスト（デフォルト: localhost）
--port PORT                  WebSocketサーバーのポート（デフォルト: 8765）
--mcp-port PORT              MCPサーバーのポート（デフォルト: 3001）
--no-console                 対話型コンソールを無効化
--disable-auth               認証を無効化（セキュリティリスクに注意）
```

### Claude Desktopでの使用

Claude Desktopの設定ファイル（`claude_desktop_config.json`）に以下を追加：

**注**: MCPサーバーは内部的にHTTP SSE (Server-Sent Events) で通信します。以下の設定により、Claude DesktopがMCPサーバープロセスを起動し、`http://localhost:3001/sse`で通信が行われます。

#### Windows
設定ファイルの場所: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "acting-doll": {
      "command": "acting-doll-server",
      "args": [
        "--mode",
        "mcp",
        "--model-dir",
        "C:/path/to/models",
        "--mcp-port",
        "3001"
      ],
      "env": {},
      "transport": {
        "type": "sse",
        "url": "http://localhost:3001/sse"
      }
    }
  }
}
```

#### macOS/Linux
設定ファイルの場所: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "acting-doll": {
      "command": "acting-doll-server",
      "args": [
        "--mode",
        "mcp",
        "--model-dir",
        "/path/to/models",
        "--mcp-port",
        "3001"
      ],
      "env": {},
      "transport": {
        "type": "sse",
        "url": "http://localhost:3001/sse"
      }
    }
  }
}
```

MCPポートを変更する場合は、`--mcp-port`引数を追加してください：

```json
{
  "mcpServers": {
    "acting-doll": {
      "command": "acting-doll-server",
      "args": [
        "--mode",
        "mcp",
        "--model-dir",
        "/path/to/models",
        "--mcp-port",
        "3002"
      ],
      "env": {}
    }
  }
}
```

### Python APIとしての使用

```python
import asyncio
from websocket_server import main, MCPServerHandler

# WebSocketサーバーとして起動
asyncio.run(main())

# または、MCPサーバーのみ
async def run_mcp():
    mcp_server = MCPServerHandler()
    await mcp_server.run()

asyncio.run(run_mcp())
```

## 利用可能なツール

MCPサーバーは以下のツールを提供します：

### モデル情報取得

- `get_model_list`: 利用可能なLive2Dモデルの一覧を取得
- `get_model_info`: 指定したモデルの詳細情報（expressions、motions、parameters）を取得

### クライアント管理

- `list_clients`: 接続中のクライアント一覧を取得
- `get_client_state`: クライアントの現在の状態を取得

### モデル制御

- `set_expression`: モデルの表情を設定
- `set_motion`: モデルのモーションを再生
- `set_parameter`: モデルのパラメータを設定
- `set_eye_blink`: まばたき機能の有効/無効を設定
- `set_breath`: 呼吸エフェクトの有効/無効を設定

## 使用例

Claude Desktopで以下のようにリクエストできます：

```
# モデル一覧を取得
「利用可能なLive2Dモデルを教えて」

# クライアント一覧を取得
「接続中のクライアントを確認して」

# 表情を変更
「クライアント127.0.0.1:12345の表情をsmileに変更して」

# モーションを再生
「クライアント127.0.0.1:12345にTapBodyモーションの0番を再生して」

# まばたきを無効化
「クライアント127.0.0.1:12345のまばたきを無効にして」
```

## トラブルシューティング

### WebSocketサーバーに接続できない

エラーメッセージ: `WebSocketサーバー (ws://localhost:8766) に接続できませんでした`

**解決方法:**
1. WebSocketサーバーが起動しているか確認
2. ホストとポート番号が正しいか確認
3. ファイアウォールの設定を確認

### タイムアウトエラー

エラーメッセージ: `タイムアウト: サーバーからの応答がありません`

**解決方法:**
1. WebSocketサーバーが正常に動作しているか確認
2. コマンドが正しいか確認
3. クライアントIDが正しいか確認

## 開発

### テストの実行

```bash
pytest tests/
```

### コードフォーマット

```bash
ruff check .
ruff format .
```

### パッケージのビルド

```bash
# ビルドツールのインストール
pip install build

# パッケージのビルド
python -m build

# 生成されたファイル
# dist/acting_doll_server-0.1.0-py3-none-any.whl
# dist/acting_doll_server-0.1.0.tar.gz
```

### ローカルでのインストールテスト

```bash
# wheelからインストール
pip install dist/acting_doll_server-0.1.0-py3-none-any.whl

# または tar.gz から
pip install dist/acting_doll_server-0.1.0.tar.gz
```

### PyPIへの公開（メンテナ向け）

```bash
# twineのインストール
pip install twine

# テストPyPIに公開
python -m twine upload --repository testpypi dist/*

# 本番PyPIに公開
python -m twine upload dist/*
```

## アーキテクチャ

### ディレクトリ構造

```
src/adapter/server/
├── __init__.py              # パッケージ初期化
├── websocket_server.py      # メインサーバー（WebSocket + MCP統合）
├── moc3manager.py           # Live2Dモデル管理
├── security_config.py       # セキュリティ設定
├── pyproject.toml           # パッケージ設定
├── README.md                # このファイル
├── LICENSE                  # MITライセンス
├── SECURITY.md              # セキュリティポリシー
└── start.sh                 # 起動スクリプト
```

### データフロー

```
MCPクライアント(Claude) --HTTP SSE--> MCPサーバー(port:3001) --内部メソッド--> コマンド処理 --WebSocket--> Live2Dクライアント
WebSocketクライアント --WebSocket(8766)--> WebSocketサーバー --コマンド処理--> Live2Dクライアント
```

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。

## 関連リンク

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Live2D Cubism SDK](https://www.live2d.com/sdk/)
- [WebSocket仕様](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## セキュリティ

セキュリティの問題を発見した場合は、[SECURITY.md](SECURITY.md)を参照してください。

