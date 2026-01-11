#!/bin/bash

server_dir="/root/workspace/adapter/server"
node_dir="/root/workspace/adapter/acting_doll"

cd ${server_dir}
python3 websocket_server.py --host 0.0.0.0 --port 8765 --no-console &
cd ${node_dir}
npm run start
