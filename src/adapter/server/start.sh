#!/bin/bash

server_dir="/root/workspace/adapter/server"
node_dir="/root/workspace/adapter/acting_doll"

cd ${server_dir}
# 既存のwebsocket_serverプロセスを停止
pkill -f "websocket_server.py" || true
sleep 1

# セキュリティ設定: デフォルトでlocalhostにバインド
# 本番環境では環境変数で認証トークンとホワイトリストを設定してください:
# export WEBSOCKET_AUTH_TOKEN="your-secret-token-here"
# export WEBSOCKET_ALLOWED_DIRS="/path/to/allowed/dir1:/path/to/allowed/dir2"
# 外部アクセスを許可する場合は --host 0.0.0.0 を指定してください（認証必須）
python3 websocket_server.py --no-console &
cd ${node_dir}
npm run start
