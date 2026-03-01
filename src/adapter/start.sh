#!/bin/bash

SCRIPT_RUNNING=${SCRIPT_RUNNING:-"true"}
if [ "${SCRIPT_RUNNING}" != "true" ]; then
    pkill -f "npm" || true
    pkill -f "acting_doll_server" || true
    pkill -f "acting-doll-server" || true
    pkill -f "acting_doll_mcp" || true
    pkill -f "acting-doll-mcp" || true
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

# 外部アクセスを許可する場合は 0.0.0.0 を指定してください（認証必須）
export HOST_ADDRESS=${HOST_ADDRESS:-"0.0.0.0"}
export PORT_WEBSOCKET_NUMBER=${PORT_WEBSOCKET_NUMBER:-"8765"}
export PORT_HTTP_NUMBER=${PORT_HTTP_NUMBER:-"5000"}
export PORT_MCP_NUMBER=${PORT_MCP_NUMBER:-"3001"}
export MODE_MCP=${MODE_MCP:-"shttp"}

export CUBISM_MODEL_DIR=${CUBISM_MODEL_DIR:-"/root/workspace/adapter/Cubism/Resource"}

###################################
if [ "${WEBSOCKET_REQUIRE_AUTH}" == "false" ] || [ -z "${WEBSOCKET_AUTH_TOKEN}" ]; then
    export WEBSOCKET_ALLOWED_DIRS=""
    export WEBSOCKET_AUTH_TOKEN=""
    export WEBSOCKET_REQUIRE_AUTH=false
fi

###################################
# Log settings
###################################
OUTPUT_LOG=${OUTPUT_LOG:-"true"}
if [ "${OUTPUT_LOG}" == "true" ]; then
    LOGS_DIR="${CURRENT_DIR}/logs"
    mkdir -p "${LOGS_DIR}"

    LOG_ACTING_DOLL_SERVER="${LOGS_DIR}/run_acting_doll_server.log"
    LOG_ACTING_DOLL_MCP="${LOGS_DIR}/run_acting_doll_mcp.log"
    LOG_NPM="${LOGS_DIR}/run_npm.log"

    rm -f "${LOG_ACTING_DOLL_SERVER}" "${LOG_ACTING_DOLL_MCP}" "${LOG_NPM}"
else
    LOG_ACTING_DOLL_SERVER="/dev/null"
    LOG_ACTING_DOLL_MCP="/dev/null"
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

###############################################################################
# Start WebSocket Server
###############################################################################
ARGS_ACTING_DOLL_SERVER="--host ${HOST_ADDRESS} --port ${PORT_WEBSOCKET_NUMBER}"
MESSAGE_ACTING_DOLL_SERVER="acting_doll_server.py"
PID_ACTING_DOLL_SERVER=-1

if [ ${ret_acting_doll} -ne 0 ]; then
    MESSAGE_ACTING_DOLL_SERVER="python3 acting_doll_server.py"
    pkill -f "acting_doll_server" || true
    # Run WebSocket server in the background
    python3 acting_doll_server.py ${ARGS_ACTING_DOLL_SERVER} >> ${LOG_ACTING_DOLL_SERVER} 2>&1 &
    PID_ACTING_DOLL_SERVER=$!
else
    acting-doll-server --version >> ${LOG_ACTING_DOLL_SERVER} 2>&1
    MESSAGE_ACTING_DOLL_SERVER="acting-doll-server"
    pkill -f ${MESSAGE_ACTING_DOLL_SERVER} || true
    # Run WebSocket server in the background
    acting-doll-server ${ARGS_ACTING_DOLL_SERVER} >> ${LOG_ACTING_DOLL_SERVER} 2>&1 &
    PID_ACTING_DOLL_SERVER=$!
fi
check_process ${PID_ACTING_DOLL_SERVER} "${MESSAGE_ACTING_DOLL_SERVER}"

###############################################################################
# Start MCP Server
###############################################################################
ARGS_ACTING_DOLL_MCP="--host ${HOST_ADDRESS} --port ${PORT_MCP_NUMBER} --mode ${MODE_MCP} --websocket_url ws://${HOST_ADDRESS}:${PORT_WEBSOCKET_NUMBER}"
MESSAGE_ACTING_DOLL_MCP="acting_doll_mcp.py"
PID_ACTING_DOLL_MCP=-1

if [ ${ret_acting_doll} -ne 0 ]; then
    MESSAGE_ACTING_DOLL_MCP="python3 acting_doll_mcp.py"
    pkill -f "acting_doll_mcp" || true
    # Run WebSocket server in the background
    python3 acting_doll_mcp.py ${ARGS_ACTING_DOLL_MCP} >> ${LOG_ACTING_DOLL_MCP} 2>&1 &
    PID_ACTING_DOLL_MCP=$!
else
    acting-doll-mcp --version >> ${LOG_ACTING_DOLL_MCP} 2>&1
    MESSAGE_ACTING_DOLL_MCP="acting-doll-mcp"
    pkill -f ${MESSAGE_ACTING_DOLL_MCP} || true
    # Run WebSocket server in the background
    acting-doll-mcp ${ARGS_ACTING_DOLL_MCP} >> ${LOG_ACTING_DOLL_MCP} 2>&1 &
    PID_ACTING_DOLL_MCP=$!
fi
check_process ${PID_ACTING_DOLL_MCP} "${MESSAGE_ACTING_DOLL_MCP}"

###################################
# Start Node.js Application
###################################
cd ${NODE_DIR}
npm run start -- --port ${PORT_HTTP_NUMBER} --host ${HOST_ADDRESS} > ${LOG_NPM} 2>&1

###################################
# Clean up: Stop application exits
###################################
kill ${PID_ACTING_DOLL_SERVER} 2>/dev/null || true
kill ${PID_ACTING_DOLL_MCP} 2>/dev/null || true

pkill -f "acting_doll_server" || true
pkill -f "acting-doll-server" || true
pkill -f "acting_doll_mcp" || true
pkill -f "acting-doll-mcp" || true
