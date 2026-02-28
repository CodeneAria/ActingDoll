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
# Define paths
###################################
CURRENT_DIR=$(dirname "$(readlink -f "$0")")
#CURRENT_DIR=$(pwd)
SERVER_DIR=$(readlink -f "${CURRENT_DIR}/server")
NODE_DIR=$(readlink -f "${CURRENT_DIR}/acting_doll")

###################################
# Settings
###################################
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

# 外部アクセスを許可する場合は 0.0.0.0 を指定してください（認証必須）
HOST_ADDRESS=${HOST_ADDRESS:-"0.0.0.0"}

PORT_WEBSOCKET_NUMBER=${PORT_WEBSOCKET_NUMBER:-"8765"}
PORT_HTTP_NUMBER=${PORT_HTTP_NUMBER:-"5000"}
PORT_MCP_NUMBER=${PORT_MCP_NUMBER:-"3001"}

MODE_MCP=${MODE_MCP:-"shttp"}

###################################
# Log settings
###################################
OUTPUT_LOG=${OUTPUT_LOG:-"true"}
if [ "${OUTPUT_LOG}" == "true" ]; then
    LOGS_DIR="${CURRENT_DIR}/logs"
    rm -rf "${LOGS_DIR}"
    mkdir -p "${LOGS_DIR}"

    LOG_ACTING_DOLL="${LOGS_DIR}/acting_doll.log"
    LOG_NPM="${LOGS_DIR}/npm.log"
else
    LOG_ACTING_DOLL="/dev/null"
    LOG_NPM="/dev/null"
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
pip show acting-doll-server > /dev/null 2>&1
ret_acting_doll=$?
ACTING_DOLL_ARGS="--host ${HOST_ADDRESS} --port ${PORT_WEBSOCKET_NUMBER} --mcp-port ${PORT_MCP_NUMBER} --mode_mcp ${MODE_MCP}"
# Cubism Controllerを起動
MESSAGE_PROCESS="acting_doll_server.py "
CUBISM_PID=-1
if [ ${ret_acting_doll} -ne 0 ]; then
    MESSAGE_PROCESS="python3 acting_doll_server.py"
    pkill -f ${MESSAGE_PROCESS} || true
    # Run WebSocket server in the background
    python3 acting_doll_server.py ${ACTING_DOLL_ARGS} > ${LOG_ACTING_DOLL} 2>&1 &
    CUBISM_PID=$!
else
    acting-doll-server --version
    MESSAGE_PROCESS="acting-doll-server"
    pkill -f ${MESSAGE_PROCESS} || true
    # Run WebSocket server in the background
    acting-doll-server ${ACTING_DOLL_ARGS} > ${LOG_ACTING_DOLL} 2>&1 &
    CUBISM_PID=$!
fi
check_process ${CUBISM_PID} "${MESSAGE_PROCESS}"


###################################
# Start Node.js Application
###################################
cd ${NODE_DIR}
npm run start -- --port ${PORT_HTTP_NUMBER} --host ${HOST_ADDRESS} > ${LOG_NPM} 2>&1

###################################
# Clean up: Stop application exits
###################################
pkill -f "acting_doll_server" || true
pkill -f "acting-doll-server" || true
