"""
WebSocket Server for bidirectional communication
サーバー側のWebSocket通信アプリケーション
"""
import argparse
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Set
import moc3manager
import websockets
from websockets.server import WebSocketServerProtocol

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 接続されたクライアントを管理
connected_clients: Set[WebSocketServerProtocol] = set()
# クライアントIDとWebSocket接続のマッピング
client_id_map: dict[str, WebSocketServerProtocol] = {}

# グローバルなモデルマネージャー（後で初期化）
model_manager = None


async def broadcast_message(message: dict, exclude: WebSocketServerProtocol = None):
    """
    全クライアントにメッセージをブロードキャスト

    Args:
        message: 送信するメッセージ（辞書形式）
        exclude: 除外するクライアント接続
    """
    if connected_clients:
        message_json = json.dumps(message, ensure_ascii=False)
        # 送信失敗したクライアントを追跡
        disconnected = set()

        for client in connected_clients:
            if client != exclude:
                try:
                    await client.send(message_json)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)

        # 切断されたクライアントを削除
        connected_clients.difference_update(disconnected)


async def send_to_client(client_id: str, message: dict) -> bool:
    """
    特定のクライアントにメッセージを送信

    Args:
        client_id: 送信先のクライアントID
        message: 送信するメッセージ（辞書形式）

    Returns:
        送信成功ならTrue、失敗ならFalse
    """
    if client_id not in client_id_map:
        logger.warning(f"クライアント {client_id} が見つかりません")
        return False

    websocket = client_id_map[client_id]
    message_json = json.dumps(message, ensure_ascii=False)

    try:
        await websocket.send(message_json)
        return True
    except websockets.exceptions.ConnectionClosed:
        logger.warning(f"クライアント {client_id} への送信に失敗（切断済み）")
        # クリーンアップ
        connected_clients.discard(websocket)
        client_id_map.pop(client_id, None)
        return False
    except Exception as e:
        logger.error(f"クライアント {client_id} への送信エラー: {e}")
        return False


def get_client_id(websocket: WebSocketServerProtocol) -> str:
    """
    WebSocket接続からクライアントIDを生成

    Args:
        websocket: WebSocket接続

    Returns:
        クライアントID
    """
    try:
        remote = websocket.remote_address
        if remote:
            return f"{remote[0]}:{remote[1]}"
        else:
            return "unknown"
    except Exception:
        return "unknown"


async def handle_client(websocket: WebSocketServerProtocol):
    """
    クライアント接続を処理

    Args:
        websocket: WebSocket接続
    """
    logger.info(f"クライアント接続要求を受信")

    # クライアントIDを生成
    client_id = get_client_id(websocket)
    logger.info(f"新しいクライアント接続: {client_id}")

    # クライアントを登録
    connected_clients.add(websocket)
    client_id_map[client_id] = websocket

    try:
        # 接続通知を他のクライアントにブロードキャスト
        await broadcast_message({
            "type": "client_connected",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "total_clients": len(connected_clients)
        }, exclude=websocket)

        # ウェルカムメッセージを送信
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "WebSocketサーバーに接続しました",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }, ensure_ascii=False))

        # メッセージ受信ループ
        async for message in websocket:
            try:
                # JSON形式で受信
                data = json.loads(message)
                logger.info(f"受信 from {client_id}: {data}")

                # メッセージタイプに応じて処理
                msg_type = data.get("type", "message")

                if msg_type == "echo":
                    # エコーバック
                    response = {
                        "type": "echo_response",
                        "original": data,
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send(json.dumps(response, ensure_ascii=False))

                elif msg_type == "broadcast":
                    # 全クライアントにブロードキャスト
                    broadcast_data = {
                        "type": "broadcast_message",
                        "from": client_id,
                        "content": data.get("content"),
                        "timestamp": datetime.now().isoformat()
                    }
                    await broadcast_message(broadcast_data)

                elif msg_type == "command":
                    # コマンド処理の例
                    command = data.get("command")
                    response = await process_command(command, client_id)
                    await websocket.send(json.dumps(response, ensure_ascii=False))

                elif msg_type == "model_command":
                    # モデルコマンド処理
                    command = data.get("command")
                    args = data.get("args", "")
                    response = await model_command(command, args)
                    await websocket.send(json.dumps(response, ensure_ascii=False))

                else:
                    # その他のメッセージは全クライアントに転送
                    forward_data = {
                        "type": "message",
                        "from": client_id,
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    }
                    await broadcast_message(forward_data, exclude=websocket)

            except json.JSONDecodeError:
                logger.error(f"不正なJSON形式: {message}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "不正なJSON形式です"
                }, ensure_ascii=False))

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"クライアント切断: {client_id}")
    except Exception as e:
        logger.error(f"エラー発生 ({client_id}): {e}")
    finally:
        # クライアントを削除
        connected_clients.discard(websocket)
        client_id_map.pop(client_id, None)

        # 切断通知をブロードキャスト
        await broadcast_message({
            "type": "client_disconnected",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "total_clients": len(connected_clients)
        })

async def model_command(command: str, args:str) -> dict:
    """
    モデル関連コマンドを処理
    Args:
        command: コマンド文字列
        client_id: クライアントID
    """
    # コマンドをパースする
    # parts = command.split(maxsplit=1)
    # cmd = parts[0].lower()
    # args = parts[1] if len(parts) > 1 else ""

    # モデル関連コマンド
    if command == "list":
        print("List:")
        print(model_manager.get_list_models())
    elif command == "get_model":
        return {
            "type": "command_response",
            "command": "get_model",
            "data": model_manager.get_models()
        }

    # モーショングループ関連コマンド
    elif command == "get_motion_groups":
        return {
            "type": "command_response",
            "command": "get_motion_groups",
            "data": model_manager.get_motion_groups()
        }
    elif command == "get_current_motion_group":
        return {
            "type": "command_response",
            "command": "get_current_motion_group",
            "data": model_manager.get_current_motion_group()
        }
    elif command == "set_motion_group":
        if not args:
            return {
                "type": "command_response",
                "command": "set_motion_group",
                "error": "モーショングループ名が必要です"
            }
        success = model_manager.set_current_motion_group(args)
        return {
            "type": "command_response",
            "command": "set_motion_group",
            "data": {
                "success": success,
                "motion_group": args if success else None
            }
        }

    # モーション関連コマンド
    elif command == "get_motions":
        group = args or model_manager.get_current_motion_group()
        return {
            "type": "command_response",
            "command": "get_motions",
            "data": {
                "motion_group": group,
                "motions": model_manager.get_motions(group)
            }
        }
    elif command == "get_current_motion":
        return {
            "type": "command_response",
            "command": "get_current_motion",
            "data": {
                "motion_group": model_manager.get_current_motion_group(),
                "motion_index": model_manager.get_current_motion_index(),
                "motion": model_manager.get_current_motion()
            }
        }
    elif command == "set_motion_index":
        try:
            index = int(args)
            success = model_manager.set_current_motion_index(index)
            return {
                "type": "command_response",
                "command": "set_motion_index",
                "data": {
                    "success": success,
                    "motion_index": index if success else None,
                    "motion": model_manager.get_current_motion() if success else None
                }
            }
        except ValueError:
            return {
                "type": "command_response",
                "command": "set_motion_index",
                "error": "有効な数値を指定してください"
            }
    elif command == "next_motion":
        motion = model_manager.next_motion()
        return {
            "type": "command_response",
            "command": "next_motion",
            "data": {
                "motion_group": model_manager.get_current_motion_group(),
                "motion_index": model_manager.get_current_motion_index(),
                "motion": motion
            }
        }
    elif command == "previous_motion":
        motion = model_manager.previous_motion()
        return {
            "type": "command_response",
            "command": "previous_motion",
            "data": {
                "motion_group": model_manager.get_current_motion_group(),
                "motion_index": model_manager.get_current_motion_index(),
                "motion": motion
            }
        }
    elif command == "get_model_info":
        model_name = args if args else None
        return {
            "type": "command_response",
            "command": "get_model_info",
            "data": model_manager.get_model_info(model_name)
        }

    else:
        return {
            "type": "command_response",
            "command": command,
            "error": "不明なコマンドです"
        }


async def process_command(command: str, client_id: str) -> dict:
    """
    コマンドを処理

    Args:
        command: コマンド文字列
        client_id: クライアントID

    Returns:
        レスポンス辞書
    """
    if command == "status":
        return {
            "type": "command_response",
            "command": "status",
            "data": {
                "connected_clients": len(connected_clients),
                "server_time": datetime.now().isoformat()
            }
        }
    elif command == "ping":
        return {
            "type": "command_response",
            "command": "ping",
            "data": "pong"
        }
    else:
        return {
            "type": "command_response",
            "command": command,
            "error": "不明なコマンドです"
        }


def print_server_console():
    print("=== サーバーコンソール ===")
    print("コマンド:")
    print("  quit                       - サーバーを停止")
    print("  count                      - 接続数を表示")
    print("  list                       - 接続中のクライアント一覧")
    print("  notify <message>           - 全クライアントに通知を送信")
    print("  send <client_id> <message> - 特定のクライアントにメッセージを送信")
    print("モデルコマンド:")
    print("  model get_model <client_id>   - 現在のモデルを取得")
    print("  model list                    - 利用可能なモデル一覧を取得")
    print("  model get_model_info [name]   - モデルの詳細情報を取得")
    print("  model get_motion_groups       - モーショングループ一覧を取得")
    print("  model get_current_motion_group- 現在のモーショングループを取得")
    print("  model get_motions [group]     - モーション一覧を取得")
    print("  model get_current_motion      - 現在のモーションを取得")
    print("  model set_motion_group <name> - モーショングループを変更")
    print("  model set_motion_index <idx>  - モーションインデックスを設定")
    print("  model motion_start            - モーションを開始")
    print("========================\n")

async def server_console():
    """
    サーバーコンソール - サーバーから能動的にメッセージを送信
    """
    print_server_console()

    while True:
        try:
            # 非同期で標準入力を読み取り
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, input, "[SERVER] > "
            )

            if not user_input.strip():
                continue

            parts = user_input.strip().split(maxsplit=1)
            command = parts[0].lower()

            if command == "quit":
                logger.info("サーバーを停止します...")
                break


            elif command == "send" and len(parts) > 1:
                # 形式: send <client_id> <message>
                send_parts = parts[1].split(maxsplit=1)
                if len(send_parts) < 2:
                    logger.warning("使い方: send <client_id> <message>")
                    continue

                target_client_id = send_parts[0]
                message = send_parts[1]

                success = await send_to_client(target_client_id, {
                    "type": "server_direct_message",
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                })

                if success:
                    logger.info(f"メッセージ送信完了 -> {target_client_id}: {message}")
                else:
                    logger.error(f"メッセージ送信失敗 -> {target_client_id}")

            elif command == "notify" and len(parts) > 1:
                message = parts[1]
                await broadcast_message({
                    "type": "server_notification",
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"通知送信: {message}")

            elif command == "list":
                if client_id_map:
                    logger.info(f"接続中のクライアント ({len(client_id_map)}件):")
                    for i, client_id in enumerate(client_id_map.keys(), 1):
                        logger.info(f"  {i}. {client_id}")
                else:
                    logger.info("接続中のクライアントはありません")

            elif command == "count":
                logger.info(f"接続数: {len(connected_clients)}")

            elif command == "model" and len(parts) > 1:
                sub_command = parts[1]
                args = parts[2] if len(parts) > 2 else ""
                await model_command(sub_command, args)

            else:
                logger.warning(f"不明なコマンド: {command}")
                print_server_console()

        except EOFError:
            break
        except Exception as e:
            logger.error(f"コンソールエラー: {e}")


async def send_periodic_messages():
    """
    定期的なメッセージ送信（オプション）
    必要に応じて有効化
    """
    while True:
        await asyncio.sleep(60)  # 60秒ごと
        if connected_clients:
            await broadcast_message({
                "type": "server_heartbeat",
                "message": "サーバーは正常に動作中",
                "timestamp": datetime.now().isoformat(),
                "connected_clients": len(connected_clients)
            })


def parse_args():
    """
    コマンドライン引数をパース
    """
    parser = argparse.ArgumentParser(
        description='WebSocket Server for Live2D model control'
    )
    parser.add_argument(
        '--model-dir',
        type=str,
        default=os.environ.get('CUBISM_MODEL_DIR', 'src/models'),
        help='モデルディレクトリのパス (デフォルト: src/models, 環境変数: CUBISM_MODEL_DIR)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='サーバーのホスト (デフォルト: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8765,
        help='サーバーのポート (デフォルト: 8765)'
    )
    return parser.parse_args()


async def main():
    """
    WebSocketサーバーを起動
    """
    global model_manager

    # コマンドライン引数をパース
    args = parse_args()

    # モデルマネージャーを初期化
    model_manager = moc3manager.ModelManager(args.model_dir)
    logger.info(f"モデルディレクトリ: {args.model_dir}")

    host = args.host
    port = args.port

    logger.info(f"WebSocketサーバーを起動中: ws://{host}:{port}")

    async with websockets.serve(handle_client, host, port):
        logger.info("サーバーが起動しました。Ctrl+Cで停止します。")

        # サーバーコンソールを起動
        console_task = asyncio.create_task(server_console())

        # オプション: 定期メッセージを有効にする場合はコメントを外す
        # periodic_task = asyncio.create_task(send_periodic_messages())

        # コンソールタスクが終了するまで待機
        await console_task

        # オプション: 定期メッセージタスクをキャンセル
        # periodic_task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nサーバーを停止しました")
