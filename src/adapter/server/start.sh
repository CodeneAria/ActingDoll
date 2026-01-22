#!/bin/bash

###################################
# Settings
###################################
SERVER_DIR="/root/workspace/adapter/server"
NODE_DIR="/root/workspace/adapter/acting_doll"
HOST_ADDRESS="0.0.0.0"
PORT_NUMBER="8765"

###################################
# Start WebSocket Server
###################################
cd ${SERVER_DIR}

# 既存のwebsocket_serverプロセスを停止
pkill -f "websocket_server.py" || true
sleep 1

# WebSocketサーバーを起動
# セキュリティ設定: デフォルトでlocalhostにバインド
# 本番環境では環境変数で認証トークンとホワイトリストを設定してください:
# export WEBSOCKET_AUTH_TOKEN="your-secret-token-here"
# export WEBSOCKET_ALLOWED_DIRS="/path/to/allowed/dir1:/path/to/allowed/dir2"
# 外部アクセスを許可する場合は --host 0.0.0.0 を指定してください（認証必須）
python3 websocket_server.py --host ${HOST_ADDRESS} --port ${PORT_NUMBER} --no-console &
WEBSOCKET_PID=$!

# WebSocketサーバーが正常に起動したか確認
sleep 3
if ! kill -0 ${WEBSOCKET_PID} 2>/dev/null; then
    echo "Error: WebSocket server failed to start" >&2
    exit 1
fi

# WebSocketサーバーが指定ポートでリスニングしているか確認（最大10秒待機）
MAX_RETRIES=20
RETRY_COUNT=0
PORT_READY=0

while [ ${RETRY_COUNT} -lt ${MAX_RETRIES} ]; do
    if nc -z ${HOST_ADDRESS} ${PORT_NUMBER} 2>/dev/null; then
        PORT_READY=1
        break
    fi
    sleep 0.5
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ ${PORT_READY} -eq 0 ]; then
    echo "Error: WebSocket server is not listening on port ${PORT_NUMBER}" >&2
    kill ${WEBSOCKET_PID} 2>/dev/null || true
    exit 1
fi

echo "WebSocket server started successfully (PID: ${WEBSOCKET_PID})"


###################################
# Start Node.js Application
###################################
cd ${NODE_DIR}
npm run start
