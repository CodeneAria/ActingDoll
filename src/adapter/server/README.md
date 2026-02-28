# Acting Doll Server

WebSocketとMCPプロトコルの両方をサポートする、Live2Dモデル制御用の統合サーバーです。

## 概要

このパッケージは、Live2DクライアントとのWebSocket通信と、LLM（Claude Desktop等）からのMCP経由制御の両方を1つのサーバーで実現します。Cubism ControllerとMCPサーバーは独立して制御でき、必要に応じてどちらか一方、または両方を実行できます。

## 機能

- **Cubism Controller**: Live2Dクライアントとのリアルタイム通信
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
# デフォルト（Cubism + MCP streamable-http両方起動）
acting-doll-server --disable-auth

# Cubismのみを起動（MCPを無効化）
acting-doll-server --mode_mcp none --disable-auth

# MCPのみを起動（Cubismを無効化）
acting-doll-server --mode_stop_cubism

# MCP SSEモードで起動
acting-doll-server --mode_mcp sse --disable-auth

# MCP標準入力モードで起動
acting-doll-server --mode_mcp stdin --disable-auth
```

### サーバーモード

#### デフォルトモード（推奨）

Cubism ControllerとMCP（streamable-http）を同時実行します。

```bash
acting-doll-server --host 127.0.0.1 --port 8765 --mcp-port 3001 --disable-auth
```

- WebSocket: `ws://127.0.0.1:8765`
- MCP: `http://127.0.0.1:3001/mcp` (streamable-http)
- 1つのプロセスで両方を処理

#### Cubismのみモード

Live2DクライアントとのWebSocket通信のみを行います。

```bash
acting-doll-server --mode_mcp none --port 8765 --disable-auth
```

- WebSocket: `ws://127.0.0.1:8765`
- MCPは起動しない
- コンソールから対話的にコマンド実行可能（`--console`で有効化）

#### MCPのみモード

MCP経由の制御のみを行います。

```bash
acting-doll-server --mode_stop_cubism --mode_mcp sse --mcp-port 3001
```

- MCPサーバー: `http://127.0.0.1:3001/sse` (SSE)
- Cubism Controllerは起動しない
- Claude Desktop等のMCPクライアントから使用

#### MCP SSEモード

MCPをSSE（Server-Sent Events）経由で操作する場合：

```bash
acting-doll-server --mode_mcp sse --mcp-port 3001
```

- HTTP SSE経由で通信
- エンドポイント: `http://127.0.0.1:3001/sse`

#### MCP標準入力モード

MCPを標準入力経由で操作する場合：

```bash
acting-doll-server --mode_mcp stdin --mcp-port 3001
```

- 標準入力/標準出力経由で通信
- MCPを同PC内で常時実行する場合に使用

### コマンドライン引数

| 引数                 | 型                        | デフォルト値         | 説明                                                                                               |
| -------------------- | ------------------------- | -------------------- | -------------------------------------------------------------------------------------------------- |
| `--mode_mcp`         | {shttp, sse, stdin, none} | shttp                | MCPプロトコルモード（shttp:streamable-http, sse:Server-Sent Events, stdin:標準入力, none:MCP無効） |
| `--mode_stop_cubism` | フラグ                    | False                | Cubism Controllerを無効化（このフラグが指定されるとCubismが起動しない）                            |
| `--model-dir`        | PATH                      | src/Cubism/Resources | モデルディレクトリのパス（環境変数:`CUBISM_MODEL_DIR`）                                            |
| `--host`             | HOST                      | 127.0.0.1            | WebSocketサーバーのホスト（環境変数:`WEBSOCKET_HOST`）                                             |
| `--port`             | PORT                      | 8765                 | Cubism Controllerのポート（環境変数:`WEBSOCKET_PORT`）                                             |
| `--mcp-port`         | PORT                      | 3001                 | MCPサーバーのポート                                                                                |
| `--console`          | フラグ                    | False                | 対話型コンソールを有効化（MCPが起動している場合は無視）                                            |
| `--disable-auth`     | フラグ                    | False                | 認証を無効化（セキュリティリスクに注意）                                                           |
| `--version`          | -                         | -                    | バージョン情報を表示                                                                               |

### Claude Desktopでの使用

Claude Desktopの設定ファイル（`claude_desktop_config.json`）にサーバーを追加してください。

#### Windows
設定ファイルの場所: `%APPDATA%\Claude\claude_desktop_config.json`

**streamable-httpモード（推奨）**

```json
{
  "mcpServers": {
    "acting-doll": {
      "command": "acting-doll-server",
      "args": [
        "--mode_mcp",
        "shttp",
        "--model-dir",
        "C:/path/to/models"
      ],
      "env": {}
    }
  }
}
```

**SSEモード**

```json
{
  "mcpServers": {
    "acting-doll": {
      "command": "acting-doll-server",
      "args": [
        "--mode_mcp",
        "sse",
        "--model-dir",
        "C:/path/to/models",
        "--mcp-port",
        "3001"
      ],
      "env": {}
    }
  }
}
```

#### macOS/Linux
設定ファイルの場所: `~/.config/Claude/claude_desktop_config.json`

**streamable-httpモード（推奨）**

```json
{
  "mcpServers": {
    "acting-doll": {
      "command": "acting-doll-server",
      "args": [
        "--mode_mcp",
        "shttp",
        "--model-dir",
        "/path/to/models"
      ],
      "env": {}
    }
  }
}
```

**SSEモード**

```json
{
  "mcpServers": {
    "acting-doll": {
      "command": "acting-doll-server",
      "args": [
        "--mode_mcp",
        "sse",
        "--model-dir",
        "/path/to/models",
        "--mcp-port",
        "3001"
      ],
      "env": {}
    }
  }
}
```

### Python APIとしての使用

```python
import asyncio
from acting_doll_server import main

# Cubism Controllerとして起動
asyncio.run(main())

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

### Cubism Controllerに接続できない

エラーメッセージ: `Cubism Controller (ws://localhost:8766) に接続できませんでした`

**解決方法:**
1. Cubism Controllerが起動しているか確認
2. ホストとポート番号が正しいか確認
3. ファイアウォールの設定を確認

### タイムアウトエラー

エラーメッセージ: `タイムアウト: サーバーからの応答がありません`

**解決方法:**
1. Cubism Controllerが正常に動作しているか確認
2. コマンドが正しいか確認
3. クライアントIDが正しいか確認

## セキュリティ設定

このセクションでは、Cubism Control Serverのセキュリティ設定について説明します。

### セキュリティ機能

#### 1. 認証 (Authentication)

Cubism Control Serverは、接続時にトークンベースの認証をサポートしています。

**認証を有効にする**

環境変数 `WEBSOCKET_AUTH_TOKEN` を設定して認証を有効にします。

```bash
export WEBSOCKET_AUTH_TOKEN="your-secret-token-here"
```

認証が有効な場合、クライアントは接続後に以下のメッセージを送信する必要があります：

```json
{
  "type": "auth",
  "token": "your-secret-token-here"
}
```

**認証を無効にする（開発環境のみ推奨）**

```bash
export WEBSOCKET_REQUIRE_AUTH="false"
```

**警告**: 本番環境では認証を必ず有効にしてください。

#### 2. ネットワーク制限 (Network Restrictions)

**デフォルト設定（セキュア）**

デフォルトでは、サーバーは `127.0.0.1` (localhost) にバインドされます。これにより、同じマシン上のクライアントのみが接続できます。

```bash
python3 acting_doll_server.py --host 127.0.0.1
```

**外部アクセスを許可する（認証必須）**

外部からのアクセスを許可する場合は、`--host 0.0.0.0` を指定します。**この場合、必ず認証を有効にしてください**：

```bash
export WEBSOCKET_AUTH_TOKEN="your-secret-token-here"
python3 acting_doll_server.py --host 0.0.0.0 --port 8765
```

#### 3. ファイルアクセス制限 (File Access Restrictions)

`set_lipsync_from_file` コマンドなどのファイルを読み取るコマンドは、ホワイトリストで指定されたディレクトリ内のファイルのみにアクセスできます。

**ホワイトリストの設定**

環境変数 `WEBSOCKET_ALLOWED_DIRS` にコロン区切りでディレクトリパスを指定します：

```bash
export WEBSOCKET_ALLOWED_DIRS="/path/to/audio/files:/path/to/another/allowed/dir"
```

ホワイトリストが設定されていない場合、ファイル読み取りコマンドは全て拒否されます。

### セキュリティ設定例

**開発環境（ローカルのみ、認証なし）**

```bash
export WEBSOCKET_REQUIRE_AUTH="false"
export WEBSOCKET_ALLOWED_DIRS="/home/user/workspace/audio"
python3 acting_doll_server.py
```

**本番環境（認証あり、ホワイトリストあり）**

```bash
export WEBSOCKET_HOST="0.0.0.0"
export WEBSOCKET_PORT="8765"
export WEBSOCKET_AUTH_TOKEN="$(openssl rand -base64 32)"
export WEBSOCKET_ALLOWED_DIRS="/opt/acting-doll/audio:/opt/acting-doll/data"
python3 acting_doll_server.py
```

**Dockerコンテナ内での設定**

`docker-compose.yml` で環境変数を設定：

```yaml
services:
  websocket:
    environment:
      - WEBSOCKET_AUTH_TOKEN=your-secret-token
      - WEBSOCKET_ALLOWED_DIRS=/app/audio
      - WEBSOCKET_HOST=0.0.0.0
```

または `docker run` コマンド：

```bash
docker run -e WEBSOCKET_AUTH_TOKEN=your-secret-token \
           -e WEBSOCKET_ALLOWED_DIRS=/app/audio \
           -e WEBSOCKET_HOST=0.0.0.0 \
           your-image
```

### セキュリティのベストプラクティス

1. **本番環境では必ず認証を有効にする**: `WEBSOCKET_AUTH_TOKEN` を設定し、強力なランダムトークンを使用してください。

2. **ネットワークアクセスを制限**: 可能な限り `127.0.0.1` にバインドし、必要な場合のみ外部アクセスを許可してください。

3. **ファイルアクセスを最小限に**: `WEBSOCKET_ALLOWED_DIRS` で必要最小限のディレクトリのみを許可してください。

4. **ファイアウォールを使用**: 追加のセキュリティ層として、ファイアウォール（iptables、ufw等）でポートアクセスを制限してください。

5. **トークンを安全に管理**: 認証トークンは環境変数やシークレット管理システムで管理し、コードやログに含めないでください。

6. **HTTPS/TLS を使用**: 本番環境では、リバースプロキシ（nginx、Caddy等）を使用してWSS（WebSocket Secure）を設定してください。

### セキュリティに関するトラブルシューティング

**接続が拒否される**

- 認証トークンが正しく設定されているか確認してください
- クライアントが正しい認証メッセージを送信しているか確認してください
- ホストとポートの設定が正しいか確認してください

**ファイルアクセスが拒否される**

- `WEBSOCKET_ALLOWED_DIRS` が正しく設定されているか確認してください
- ファイルパスがホワイトリストのディレクトリ内にあるか確認してください
- ファイルへの読み取り権限があるか確認してください

**外部から接続できない**

- `--host 0.0.0.0` または `WEBSOCKET_HOST=0.0.0.0` が設定されているか確認してください
- ファイアウォールでポートが開放されているか確認してください
- 認証トークンが設定されているか確認してください

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
# dist/acting_doll_server-*-py3-none-any.whl
# dist/acting_doll_server-*.tar.gz
```

### ローカルでのインストールテスト

```bash
# wheelからインストール
pip install dist/acting_doll_server-*-py3-none-any.whl

# または tar.gz から
pip install dist/acting_doll_server-*.tar.gz
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
├── acting_doll_server.py      # メインサーバー（WebSocket + MCP統合）
├── moc3manager.py           # Live2Dモデル管理
├── security_config.py       # セキュリティ設定
├── pyproject.toml           # パッケージ設定
├── README.md                # このファイル
├── LICENSE                  # MITライセンス
└── start.sh                 # 起動スクリプト
```

### データフロー

```
MCPクライアント(Claude) --HTTP SSE--> MCPサーバー(port:3001) --内部メソッド--> コマンド処理 --WebSocket--> Live2Dクライアント
WebSocketクライアント --WebSocket(8766)--> Cubism Controller --コマンド処理--> Live2Dクライアント
```

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照してください。

## 関連リンク

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Live2D Cubism SDK](https://www.live2d.com/sdk/)
- [WebSocket仕様](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

