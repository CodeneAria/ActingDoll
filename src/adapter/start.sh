#!/bin/bash

###################################
# Settings
###################################
SERVER_DIR="/root/workspace/adapter/server"
NODE_DIR="/root/workspace/adapter/acting_doll"
# 外部アクセスを許可する場合は 0.0.0.0 を指定してください（認証必須）
HOST_ADDRESS=${HOST_ADDRESS:-"0.0.0.0"}

PORT_WEBSOCKET_NUMBER=${PORT_WEBSOCKET_NUMBER:-"8765"}
PORT_HTTP_NUMBER=${PORT_HTTP_NUMBER:-"5000"}
PORT_MCP_NUMBER=${PORT_MCP_NUMBER:-"3001"}

# セキュリティ設定: デフォルトでlocalhostにバインド
# 本番環境では環境変数で認証トークンとホワイトリストを設定してください:
export WEBSOCKET_AUTH_TOKEN=${WEBSOCKET_AUTH_TOKEN:-"your_secret_token_here"}
export WEBSOCKET_ALLOWED_DIRS=${WEBSOCKET_ALLOWED_DIRS:-"/root/workspace/adapter/allowed"}
export WEBSOCKET_REQUIRE_AUTH=${WEBSOCKET_REQUIRE_AUTH:-"false"}

###################################
# Function
###################################
# WebSocketサーバーが正常に起動したか確認
function check_process {
    local CH_PID=${1}
    local CH_NAME=${2}

    local MAX_RETRIES=20
    local RETRY_COUNT=0
    local PORT_READY=0
    while [ ${RETRY_COUNT} -lt ${MAX_RETRIES} ]; do
        if kill -0 ${CH_PID} 2>/dev/null; then
            PORT_READY=1
            break
        fi
        sleep 0.5
        RETRY_COUNT=$((RETRY_COUNT + 1))
    done

    if [ ${PORT_READY} -eq 0 ]; then
        echo "Error: ${CH_NAME} failed to start" >&2
        kill ${CH_PID} 2>/dev/null || true
        exit 1
    fi
}
###################################
# Start WebSocket Server
###################################
cd ${SERVER_DIR}

# 既存のwebsocket_serverプロセスを停止
pip show acting-doll >/dev/null 2>&1
ret_acting_doll=$?
# WebSocketサーバーを起動
pkill -f "acting_doll_server" || true
if [ ${ret_acting_doll} -ne 0 ]; then
    # Run WebSocket server in the background
    python3 acting_doll_server.py --mode websocket --host ${HOST_ADDRESS} --port ${PORT_WEBSOCKET_NUMBER} --no-console &
    WEBSOCKET_PID=$!
    check_process ${WEBSOCKET_PID} "WebSocket Server"
    sleep 1
    # Run MCP server in the background
    python3 acting_doll_server.py --mode mcp --host ${HOST_ADDRESS} --mcp-port ${PORT_MCP_NUMBER} --no-console &
    MCP_PID=$!
    check_process ${MCP_PID} "MCP Server"
    echo "# 'acting_doll_server.py' started successfully (WebSocket PID: ${WEBSOCKET_PID}, MCP PID: ${MCP_PID})"
else
    # Run WebSocket server in the background
    acting-doll-server --mode websocket --host ${HOST_ADDRESS} --port ${PORT_WEBSOCKET_NUMBER} --no-console &
    WEBSOCKET_PID=$!
    check_process ${WEBSOCKET_PID} "WebSocket Server"
    sleep 1
    # Run MCP server in the background
    acting-doll-server --mode mcp --host ${HOST_ADDRESS} --mcp-port ${PORT_MCP_NUMBER} --no-console &
    MCP_PID=$!
    check_process ${MCP_PID} "MCP Server"

    echo "# 'acting-doll-server' started successfully (WebSocket PID: ${WEBSOCKET_PID}, MCP PID: ${MCP_PID})"
fi


sleep 1

###################################
# Start Node.js Application
###################################
cd ${NODE_DIR}
npm run start -- --port ${PORT_HTTP_NUMBER} --host ${HOST_ADDRESS}

# Clean up: Stop WebSocket and MCP servers when Node.js application exits
pkill -f "acting_doll_server" || true
