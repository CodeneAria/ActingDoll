#!/bin/bash

server_dir="/root/workspace/adapter/server"
node_dir="/root/workspace/adapter/acting_doll"

cd ${server_dir}
# 既存のwebsocket_serverプロセスを停止
pkill -f "websocket_server.py" || true
sleep 1

# WebSocketサーバーを起動
python3 websocket_server.py --host 0.0.0.0 --port 8765 --no-console &
WEBSOCKET_PID=$!

# WebSocketサーバーが正常に起動したか確認
sleep 3
if ! kill -0 $WEBSOCKET_PID 2>/dev/null; then
    echo "Error: WebSocket server failed to start" >&2
    exit 1
fi

# WebSocketサーバーが指定ポートでリスニングしているか確認（最大10秒待機）
MAX_RETRIES=20
RETRY_COUNT=0
PORT_READY=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if nc -z localhost 8765 2>/dev/null; then
        PORT_READY=1
        break
    fi
    sleep 0.5
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $PORT_READY -eq 0 ]; then
    echo "Error: WebSocket server is not listening on port 8765" >&2
    kill $WEBSOCKET_PID 2>/dev/null || true
    exit 1
fi

echo "WebSocket server started successfully (PID: $WEBSOCKET_PID)"

cd ${node_dir}
npm run start
