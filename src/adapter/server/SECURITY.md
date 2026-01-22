# WebSocket Server Security Configuration

このドキュメントでは、WebSocketサーバーのセキュリティ設定について説明します。

## セキュリティ機能

### 1. 認証 (Authentication)

WebSocketサーバーは、接続時にトークンベースの認証をサポートしています。

#### 認証を有効にする

環境変数 `WEBSOCKET_AUTH_TOKEN` を設定して認証を有効にします：

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

#### 認証を無効にする（開発環境のみ推奨）

```bash
export WEBSOCKET_REQUIRE_AUTH="false"
```

**警告**: 本番環境では認証を必ず有効にしてください。

### 2. ネットワーク制限 (Network Restrictions)

#### デフォルト設定（セキュア）

デフォルトでは、サーバーは `127.0.0.1` (localhost) にバインドされます。これにより、同じマシン上のクライアントのみが接続できます。

```bash
python3 websocket_server.py
# または
python3 websocket_server.py --host 127.0.0.1
```

#### 外部アクセスを許可する（認証必須）

外部からのアクセスを許可する場合は、`--host 0.0.0.0` を指定します。**この場合、必ず認証を有効にしてください**：

```bash
export WEBSOCKET_AUTH_TOKEN="your-secret-token-here"
python3 websocket_server.py --host 0.0.0.0 --port 8765
```

または環境変数で設定：

```bash
export WEBSOCKET_HOST="0.0.0.0"
export WEBSOCKET_PORT="8765"
export WEBSOCKET_AUTH_TOKEN="your-secret-token-here"
python3 websocket_server.py
```

### 3. ファイルアクセス制限 (File Access Restrictions)

`set_lipsync_from_file` コマンドなどのファイルを読み取るコマンドは、ホワイトリストで指定されたディレクトリ内のファイルのみにアクセスできます。

#### ホワイトリストの設定

環境変数 `WEBSOCKET_ALLOWED_DIRS` にコロン区切りでディレクトリパスを指定します：

```bash
export WEBSOCKET_ALLOWED_DIRS="/path/to/audio/files:/path/to/another/allowed/dir"
```

#### デフォルト動作

ホワイトリストが設定されていない場合、ファイル読み取りコマンドは全て拒否されます。

## 設定例

### 開発環境（ローカルのみ、認証なし）

```bash
export WEBSOCKET_REQUIRE_AUTH="false"
export WEBSOCKET_ALLOWED_DIRS="/home/user/workspace/audio"
python3 websocket_server.py
```

### 本番環境（認証あり、ホワイトリストあり）

```bash
export WEBSOCKET_HOST="0.0.0.0"
export WEBSOCKET_PORT="8765"
export WEBSOCKET_AUTH_TOKEN="$(openssl rand -base64 32)"
export WEBSOCKET_ALLOWED_DIRS="/opt/actingdoll/audio:/opt/actingdoll/data"
python3 websocket_server.py --no-console
```

### Dockerコンテナ内での設定

`docker-compose.yml` または `docker run` コマンドで環境変数を設定：

```yaml
services:
  websocket:
    environment:
      - WEBSOCKET_AUTH_TOKEN=your-secret-token
      - WEBSOCKET_ALLOWED_DIRS=/app/audio
      - WEBSOCKET_HOST=0.0.0.0
```

または：

```bash
docker run -e WEBSOCKET_AUTH_TOKEN=your-secret-token \
           -e WEBSOCKET_ALLOWED_DIRS=/app/audio \
           -e WEBSOCKET_HOST=0.0.0.0 \
           your-image
```

## セキュリティのベストプラクティス

1. **本番環境では必ず認証を有効にする**: `WEBSOCKET_AUTH_TOKEN` を設定し、強力なランダムトークンを使用してください。

2. **ネットワークアクセスを制限**: 可能な限り `127.0.0.1` にバインドし、必要な場合のみ外部アクセスを許可してください。

3. **ファイルアクセスを最小限に**: `WEBSOCKET_ALLOWED_DIRS` で必要最小限のディレクトリのみを許可してください。

4. **ファイアウォールを使用**: 追加のセキュリティ層として、ファイアウォール（iptables、ufw等）でポートアクセスを制限してください。

5. **トークンを安全に管理**: 認証トークンは環境変数やシークレット管理システムで管理し、コードやログに含めないでください。

6. **HTTPS/TLS を使用**: 本番環境では、リバースプロキシ（nginx、Caddy等）を使用してWSS（WebSocket Secure）を設定してください。

## トラブルシューティング

### 接続が拒否される

- 認証トークンが正しく設定されているか確認してください
- クライアントが正しい認証メッセージを送信しているか確認してください
- ホストとポートの設定が正しいか確認してください

### ファイルアクセスが拒否される

- `WEBSOCKET_ALLOWED_DIRS` が正しく設定されているか確認してください
- ファイルパスがホワイトリストのディレクトリ内にあるか確認してください
- ファイルへの読み取り権限があるか確認してください

### 外部から接続できない

- `--host 0.0.0.0` または `WEBSOCKET_HOST=0.0.0.0` が設定されているか確認してください
- ファイアウォールでポートが開放されているか確認してください
- 認証トークンが設定されているか確認してください
