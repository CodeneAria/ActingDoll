#!/bin/bash

SCRIPT_RUNNING=${SCRIPT_RUNNING:-"true"}
if [ "${SCRIPT_RUNNING}" != "true" ]; then
    pkill -f "npm" || true
    pkill -f "acting_doll_server" || true
    pkill -f "acting-doll-server" || true
    echo "# Stop command received. Exiting start script."
    exit 0
fi

###################################
# Settings
###################################
CURRENT_DIR=$(dirname "$(readlink -f "$0")")
SERVER_DIR=$(readlink -f "${CURRENT_DIR}/server")
NODE_DIR=$(readlink -f "${CURRENT_DIR}/acting_doll")
# 外部アクセスを許可する場合は 0.0.0.0 を指定してください（認証必須）
HOST_ADDRESS=${HOST_ADDRESS:-"0.0.0.0"}

PORT_WEBSOCKET_NUMBER=${PORT_WEBSOCKET_NUMBER:-"8765"}
PORT_HTTP_NUMBER=${PORT_HTTP_NUMBER:-"5000"}
PORT_MCP_NUMBER=${PORT_MCP_NUMBER:-"3001"}

# セキュリティ設定: デフォルトでlocalhostにバインド
# 本番環境では環境変数で認証トークンとホワイトリストを設定してください:
export WEBSOCKET_AUTH_TOKEN=${WEBSOCKET_AUTH_TOKEN:-"your_secret_token_here"}
export WEBSOCKET_ALLOWED_DIRS=${WEBSOCKET_ALLOWED_DIRS:-"${CURRENT_DIR}/allowed"}
export WEBSOCKET_REQUIRE_AUTH=${WEBSOCKET_REQUIRE_AUTH:-"false"}

if [ "${WEBSOCKET_REQUIRE_AUTH}" == "false" ] || [ -z "${WEBSOCKET_AUTH_TOKEN}" ]; then
    export WEBSOCKET_ALLOWED_DIRS=""
    export WEBSOCKET_AUTH_TOKEN=""
    export WEBSOCKET_REQUIRE_AUTH=false
fi

###################################
# Function
###################################
# Cubism Controllerが正常に起動したか確認
function check_process {
    local CH_PID=${1}
    local CH_NAME=${2}

    local MAX_RETRIES=15
    local RETRY_COUNT=0
    local PORT_READY=0
    while [ ${RETRY_COUNT} -lt ${MAX_RETRIES} ]; do
        if kill -0 ${CH_PID} 2>/dev/null; then
            PORT_READY=1
        else
            PORT_READY=0
            break
        fi
        sleep 0.5
        RETRY_COUNT=$((RETRY_COUNT + 1))
        #echo "Waiting for '${CH_NAME}' to start... (Retry ${RETRY_COUNT}/${MAX_RETRIES})[${PORT_READY}]"
    done

    if [ ${PORT_READY} -eq 0 ]; then
        echo "Error: ${CH_NAME} failed to start" >&2
        kill ${CH_PID} 2>/dev/null || true
        exit 1
    fi
    echo "# '${CH_NAME}' started successfully (PID: ${CH_PID})"
}
###################################
# Start Server
###################################
cd ${SERVER_DIR}

# 既存のCubism Controllerプロセスを停止
pip show acting-doll-server >/dev/null 2>&1
ret_acting_doll=$?
# Cubism Controllerを起動
MESSAGE_PROCESS="acting_doll_server.py "
CUBISM_PID=-1
pkill -f "acting_doll_server" || true
if [ ${ret_acting_doll} -ne 0 ]; then
    MESSAGE_PROCESS="python3 acting_doll_server.py"
    # Run WebSocket server in the background
    python3 acting_doll_server.py --host ${HOST_ADDRESS} --port ${PORT_WEBSOCKET_NUMBER} --mcp-port ${PORT_MCP_NUMBER} &
    CUBISM_PID=$!
else
    acting-doll-server --version
    MESSAGE_PROCESS="acting-doll-server"
    # Run WebSocket server in the background
    acting-doll-server --host ${HOST_ADDRESS} --port ${PORT_WEBSOCKET_NUMBER} --mcp-port ${PORT_MCP_NUMBER} &
    CUBISM_PID=$!
fi
check_process ${CUBISM_PID} "${MESSAGE_PROCESS}"


###################################
# Start Node.js Application
###################################
cd ${NODE_DIR}
npm run start -- --port ${PORT_HTTP_NUMBER} --host ${HOST_ADDRESS}

###################################
# Clean up: Stop application exits
###################################
pkill -f "acting_doll_server" || true
pkill -f "acting-doll-server" || true
