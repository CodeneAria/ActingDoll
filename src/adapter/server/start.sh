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
sleep 2
if ! kill -0 $WEBSOCKET_PID 2>/dev/null; then
    echo "Error: WebSocket server failed to start" >&2
    exit 1
fi

# WebSocketサーバーが指定ポートでリスニングしているか確認
if ! timeout 10 bash -c "until nc -z localhost 8765; do sleep 0.5; done" 2>/dev/null; then
    echo "Error: WebSocket server is not listening on port 8765" >&2
    kill $WEBSOCKET_PID 2>/dev/null || true
    exit 1
fi

echo "WebSocket server started successfully (PID: $WEBSOCKET_PID)"

cd ${node_dir}
npm run start
