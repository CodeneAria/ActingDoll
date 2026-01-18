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
from websockets.server import ServerConnection

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 接続されたクライアントを管理
connected_clients: Set[ServerConnection] = set()
# クライアントIDとWebSocket接続のマッピング
client_id_map: dict[str, ServerConnection] = {}

# グローバルなモデルマネージャー（後で初期化）
model_manager = None


async def broadcast_message(message: dict, exclude: ServerConnection = None):
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


def get_client_id(websocket: ServerConnection) -> str:
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


async def handle_client(websocket: ServerConnection):
    """
    クライアント接続を処理

    Args:
        websocket: WebSocket接続
    """
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
            "message": "Welcome to the WebSocket server!",
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
                    logger.info(f"{client_id}::{response}")
                    await websocket.send(json.dumps(response, ensure_ascii=False))

                elif msg_type == "model":
                    # モデルコマンド処理
                    command = data.get("command")
                    args = data.get("args", "")
                    response = await model_command(command, args)
                    await websocket.send(json.dumps(response, ensure_ascii=False))

                elif msg_type == "client":
                    # クライアント状態管理コマンド処理
                    command = data.get("command")
                    args = data.get("args", {})
                    response = await client_command(command, args, client_id)
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


async def model_command(command: str, args: str) -> dict:
    """
    モデル関連コマンドを処理
    Args:
        command: コマンド文字列
        args: コマンド引数
    Returns:
        レスポンス辞書
    """
    # 1. model list - 利用可能なモデル一覧を取得
    if command == "list":
        models = model_manager.get_models()
        logger.info(f"利用可能なモデル: {models}")
        return {
            "type": "command_response",
            "command": "list",
            "data": models
        }

    # 2. model get_expressions <model_name> - モデルのexpressionsを取得
    elif command == "get_expressions":
        if not args:
            return {
                "type": "command_response",
                "command": "get_expressions",
                "error": "モデル名が必要です"
            }
        model_info = model_manager.get_model_info(args)
        if model_info:
            expressions = model_info.get(
                'FileReferences', {}).get('Expressions', [])
            expression_names = [exp.get('Name') for exp in expressions]
            logger.info(f"expressions一覧: {expression_names}")
            return {
                "type": "command_response",
                "command": "get_expressions",
                "data": {
                    "model_name": args,
                    "expressions": expressions
                }
            }
        return {
            "type": "command_response",
            "command": "get_expressions",
            "error": f"モデル '{args}' が見つかりません"
        }

    # 3. model get_motions <model_name> - モデルのmotionsを取得
    elif command == "get_motions":
        if not args:
            return {
                "type": "command_response",
                "command": "get_motions",
                "error": "モデル名が必要です"
            }
        model_info = model_manager.get_model_info(args)
        if model_info:
            motions = model_info.get('FileReferences', {}).get('Motions', {})
            motion_summary = {}
            for group_name, motion_list in motions.items():
                motion_summary[group_name] = [
                    m.get('File') for m in motion_list]
            logger.info(f"motions一覧: {motion_summary}")
            return {
                "type": "command_response",
                "command": "get_motions",
                "data": {
                    "model_name": args,
                    "motions": motions
                }
            }
        return {
            "type": "command_response",
            "command": "get_motions",
            "error": f"モデル '{args}' が見つかりません"
        }

    # 4. model get_parameters <model_name> - モデルのparametersを取得
    elif command == "get_parameters":
        if not args:
            return {
                "type": "command_response",
                "command": "get_parameters",
                "error": "モデル名が必要です"
            }
        parameters = model_manager.get_parameters_exclude_physics(args)
        if parameters:
            # Id, Name, GroupIdを抽出して表示用に整形
            param_summary = []
            for param in parameters:
                param_summary.append({
                    "Id": param.get('Id'),
                    "Name": param.get('Name'),
                    "GroupId": param.get('GroupId', '')
                })
            logger.info(
                f"parameters一覧 ({len(param_summary)}件): {[p['Id'] for p in param_summary]}")
            return {
                "type": "command_response",
                "command": "get_parameters",
                "data": {
                    "model_name": args,
                    "parameters": param_summary
                }
            }
        return {
            "type": "command_response",
            "command": "get_parameters",
            "error": f"モデル '{args}' のパラメータ情報が見つかりません"
        }

    else:
        return {
            "type": "command_response",
            "command": command,
            "error": f"不明なコマンド: {command}"
        }


async def client_command(command: str, args: dict,
                         client_id: str, source_client_id: str = "") -> dict:
    """
    クライアント状態管理コマンドを処理

    Args:
        command: コマンド文字列
        args: コマンド引数（辞書形式）
        client_id: クライアントID
        source_client_id: 送信元クライアントID
    Returns:
        レスポンス辞書
    """
    if client_id not in client_id_map:
        return {
            "type": "client",
            "command": command,
            "source": source_client_id,
            "error": f"クライアント '{client_id}' が見つかりません"
        }

    if command.startswith("response_"):
        return {
            "type": "client_response",
            "command": command,
            "success": True,
            "client_id": client_id,
            "source": source_client_id,
            "data": args,
            "message": "クライアントからレスポンスを受信しました"
        }
    elif command.startswith("set_"):
        if command == "set_eye_blink":  # アニメーション設定 - 自動目パチ
            if not args:
                return {
                    "type": "client",
                    "command": command,
                    "error": "パラメータを指定してください: enabled or disabled"
                }
            if isinstance(args, dict):
                enabled = args.get("enabled", True)
            else:
                enabled = ("enabled" in str(args).lower())
            await send_to_client(client_id, {
                "type": "set_eye_blink",
                "client_id": client_id,
                "source": source_client_id,
                "enabled": enabled,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "client_request",
                "command": "set_eye_blink",
                "success": True,
                "data": {"enabled": enabled},
                "message": "クライアントに自動目パチ設定を送信しました"
            }

        elif command == "set_breath":  # アニメーション設定 - 呼吸
            if not args:
                return {
                    "type": "client",
                    "command": command,
                    "error": "パラメータを指定してください: enabled or disabled"
                }
            if isinstance(args, dict):
                enabled = args.get("enabled", True)
            else:
                enabled = ("enabled" in str(args).lower())
            await send_to_client(client_id, {
                "type": "set_breath",
                "client_id": client_id,
                "source": source_client_id,
                "enabled": enabled,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "client_request",
                "command": "set_breath",
                "success": True,
                "data": {"enabled": enabled},
                "message": "クライアントに呼吸設定を送信しました"
            }

        elif command == "set_idle_motion":  # アニメーション設定 - アイドリングモーション
            if not args:
                return {
                    "type": "client",
                    "command": command,
                    "error": "パラメータを指定してください: enabled or disabled"
                }
            if isinstance(args, dict):
                enabled = args.get("enabled", True)
            else:
                enabled = ("enabled" in str(args).lower())
            await send_to_client(client_id, {
                "type": "set_idle_motion",
                "client_id": client_id,
                "source": source_client_id,
                "enabled": enabled,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "client_request",
                "command": "set_idle_motion",
                "success": True,
                "data": {"enabled": enabled},
                "message": "クライアントにアイドリングモーション設定を送信しました"
            }

        elif command == "set_drag_follow":  # アニメーション設定 - ドラッグ追従
            if not args:
                return {
                    "type": "client",
                    "command": command,
                    "error": "パラメータを指定してください: enabled or disabled"
                }
            if isinstance(args, dict):
                enabled = args.get("enabled", True)
            else:
                enabled = ("enabled" in str(args).lower())
            await send_to_client(client_id, {
                "type": "set_drag_follow",
                "client_id": client_id,
                "source": source_client_id,
                "enabled": enabled,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "client_request",
                "command": "set_drag_follow",
                "success": True,
                "data": {"enabled": enabled},
                "message": "クライアントにドラッグ追従設定を送信しました"
            }

        elif command == "set_physics":  # アニメーション設定 - 物理演算
            if not args:
                return {
                    "type": "client",
                    "command": command,
                    "error": "パラメータを指定してください: enabled or disabled"
                }
            if isinstance(args, dict):
                enabled = args.get("enabled", True)
            else:
                enabled = ("enabled" in str(args).lower())
            await send_to_client(client_id, {
                "type": "set_physics",
                "client_id": client_id,
                "source": source_client_id,
                "enabled": enabled,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "client_request",
                "command": "set_physics",
                "success": True,
                "data": {"enabled": enabled},
                "message": "クライアントに物理演算設定を送信しました"
            }

        elif command == "set_expression":  # Expressions
            parts = args.strip().split(maxsplit=1) if len(args) > 0 else ""
            expression = parts[0] if len(parts) > 0 else ""
            if not expression:
                return {
                    "type": "client_request",
                    "command": "set_expression",
                    "error": "expression名が必要です"
                }
            await send_to_client(client_id, {
                "type": "set_expression",
                "client_id": client_id,
                "source": source_client_id,
                "expression": expression,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "client_request",
                "command": "set_expression",
                "success": True,
                "data": {"client_id": client_id, "expression": expression},
                "message": "クライアントに表情設定を送信しました"
            }

        elif command == "set_motion":  # Motions
            parts = args.strip().split(maxsplit=2) if len(args) > 0 else ""
            group = parts[0] if len(parts) > 0 else ""
            no = parts[1] if len(parts) > 1 else ""
            priority = parts[2] if len(parts) > 2 else "2"  # デフォルトはPriorityNormal(2)

            if not group:
                return {
                    "type": "client_request",
                    "command": "set_motion",
                    "error": "motion group名が必要です"
                }
            if not no:
                return {
                    "type": "client_request",
                    "command": "set_motion",
                    "error": "motion noが必要です"
                }

            # priorityを整数に変換
            try:
                priority_int = int(priority)
                if priority_int < 0 or priority_int > 3:
                    return {
                        "type": "client_request",
                        "command": "set_motion",
                        "error": "priorityは0(None), 1(Idle), 2(Normal), 3(Force)のいずれかである必要があります"
                    }
            except ValueError:
                return {
                    "type": "client_request",
                    "command": "set_motion",
                    "error": "priorityは整数である必要があります"
                }

            await send_to_client(client_id, {
                "type": "set_motion",
                "client_id": client_id,
                "source": source_client_id,
                "group": group,
                "no": no,
                "priority": priority_int,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "client_request",
                "command": "set_motion",
                "success": True,
                "data": {"group": group, "no": no, "priority": priority_int},
                "message": "クライアントにモーション情報を送信しました"
            }

        elif command == "set_parameter":  # パラメータ設定（一括）
            # 一括設定モード: args = {"ParamAngleX": 30, "ParamAngleY": -15, ...}
            # または文字列形式: "ParamAngleX=30 ParamAngleY=-15"
            parameters = {}

            if isinstance(args, dict):
                # 既に辞書形式の場合はそのまま使用
                parameters = args
            elif isinstance(args, str):
                # 文字列形式の場合は解析してJSON形式に変換
                # 例: "ParamAngleX=30 ParamAngleY=-15 ParamEyeBallX=0.5"
                if not args.strip():
                    return {
                        "type": "client",
                        "command": command,
                        "error": "パラメータを指定してください: ParamName=value ParamName2=value2 ..."
                    }

                try:
                    # スペースで分割して各KEY=VALUEペアを処理
                    for param_pair in args.split():
                        if '=' in param_pair:
                            key, value = param_pair.split('=', 1)
                            # 値を数値に変換を試みる
                            try:
                                # 小数点を含む場合はfloat、そうでない場合はintに変換
                                if '.' in value:
                                    parameters[key] = float(value)
                                else:
                                    parameters[key] = int(value)
                            except ValueError:
                                # 数値変換に失敗した場合は文字列として扱う
                                parameters[key] = value
                        else:
                            logger.warning(f"無効なパラメータ形式: {param_pair}")
                except Exception as e:
                    return {
                        "type": "client",
                        "command": command,
                        "error": f"パラメータの解析に失敗しました: {str(e)}"
                    }
            else:
                return {
                    "type": "client",
                    "command": command,
                    "error": "パラメータは辞書形式または 'ParamName=value' 形式で指定してください"
                }

            if not parameters:
                return {
                    "type": "client",
                    "command": command,
                    "error": "有効なパラメータが指定されていません"
                }

            # クライアントにパラメータ設定を送信
            success = await send_to_client(client_id, {
                "type": "set_parameter",
                "client_id": client_id,
                "source": source_client_id,
                "parameters": parameters,
                "timestamp": datetime.now().isoformat()
            })

            if success:
                return {
                    "type": "client",
                    "command": command,
                    "success": True,
                    "client_id": client_id,
                    "parameters": parameters,
                    "message": f"パラメータ設定コマンドを送信しました（{len(parameters)}個）"
                }
            else:
                return {
                    "type": "client",
                    "command": command,
                    "error": f"パラメータ設定の送信に失敗しました"
                }

    elif command.startswith("get_"):
        if command == "get_eye_blink":  # アニメーション設定 - 自動目パチ
            await send_to_client(client_id, {
                "type": "request_eye_blink",
                "source": source_client_id,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "client_request",
                "command": "get_eye_blink",
                "client_id": client_id,
                "message": "クライアントに自動目パチ設定をリクエストしました"
            }

        elif command == "get_breath":  # アニメーション設定 - 呼吸
            await send_to_client(client_id, {
                "type": "request_breath",
                "source": source_client_id,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "client_request",
                "command": "get_breath",
                "client_id": client_id,
                "message": "クライアントに呼吸設定をリクエストしました"
            }

        elif command == "get_idle_motion":  # アニメーション設定 - アイドリングモーション
            await send_to_client(client_id, {
                "type": "request_idle_motion",
                "source": source_client_id,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "client_request",
                "command": "get_idle_motion",
                "client_id": client_id,
                "message": "クライアントにアイドリングモーション設定をリクエストしました"
            }

        elif command == "get_drag_follow":  # アニメーション設定 - ドラッグ追従
            await send_to_client(client_id, {
                "type": "request_drag_follow",
                "source": source_client_id,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "client_request",
                "command": "get_drag_follow",
                "client_id": client_id,
                "message": "クライアントにドラッグ追従設定をリクエストしました"
            }

        elif command == "get_physics":  # アニメーション設定 - 物理演算
            await send_to_client(client_id, {
                "type": "request_physics",
                "source": source_client_id,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "client_request",
                "command": "get_physics",
                "client_id": client_id,
                "message": "クライアントに物理演算設定をリクエストしました"
            }

        elif command == "get_expression":  # Expressions
            await send_to_client(client_id, {
                "type": "request_expression",
                "source": source_client_id,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "client_request",
                "command": "get_expression",
                "client_id": client_id,
                "message": "クライアントに表情設定をリクエストしました"
            }

        elif command == "get_motion":  # Motions
            await send_to_client(client_id, {
                "type": "request_motion",
                "source": source_client_id,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "client_request",
                "command": "get_motion",
                "client_id": client_id,
                "message": "クライアントにモーション情報をリクエストしました"
            }

        elif command == "get_model":  # クライアントにモデル情報要求を送信
            await send_to_client(client_id, {
                "type": "request_model_info",
                "source": source_client_id,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "client_request",
                "command": "get_model",
                "success": True,
                "message": "クライアントにモデル情報をリクエストしました"
            }

    return {
        "type": "client",
        "command": command,
        "error": f"不明なクライアントコマンド: {command}"
    }


async def process_command(user_input: str, client_id: str) -> dict:
    """
    コマンドを処理

    Args:
        command: コマンド文字列
        client_id: クライアントID

    Returns:
        レスポンス辞書
    """
    parts = user_input.strip().split(maxsplit=1)
    command = parts[0].lower()
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
    elif command == "list":
        json_data = {}
        if client_id_map:
            # コマンド送信者自身を除外したクライアントリストを作成
            other_clients = [
                cid for cid in client_id_map.keys() if cid != client_id]
            json_data = {
                "clients": other_clients,
                "count": len(other_clients)
            }
        else:
            json_data = {
                "clients": [],
                "count": 0
            }
        return {
            "type": "command_response",
            "command": command,
            "data": json_data
        }
    elif command == "notify":
        message = parts[1]
        await broadcast_message({
            "type": "notify",
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        return {
            "type": "command_response",
            "command": command,
            "message": message
        }
    elif command == "send":
        args = parts[1].strip().split(maxsplit=2)
        # 形式: send <client_id> <message>
        if len(args) < 2:
            return {
                "type": "command_response",
                "command": command,
                "error": "使い方: send <client_id> <message>"
            }

        target_client_id = args[0]
        message = args[1]

        success = await send_to_client(target_client_id, {
            "type": "send",
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        return {
            "type": "command_response",
            "command": command,
            "success": True if success else False
        }
    elif command == "model":
        return {
            "type": "command_response",
            "command": command,
            "message": "通知コマンドはサーバーコンソールから実行してください"
        }
    elif command == "client":
        return {
            "type": "command_response",
            "command": command,
            "message": "通知コマンドはサーバーコンソールから実行してください"
        }
    else:
        return {
            "type": "command_response",
            "command": command,
            "error": "不明なコマンドです"
        }


def print_server_console():
    print("=== サーバーコンソール ===")

    print("サーバーコマンド:")
    print("  quit                       - サーバーを停止")
    # print("  count                      - 接続数を表示")
    print("  list                       - 接続中のクライアント一覧")
    print("  notify <message>           - 全クライアントに通知を送信")
    print("  send <client_id> <message> - 特定のクライアントにメッセージを送信")

    print("モデルコマンド:")
    print("  model list                      - 利用可能なモデル一覧を取得")
    print("  model get_expressions <name>    - モデルのexpressions一覧を取得")
    print("  model get_motions <name>        - モデルのmotions一覧を取得")
    print("  model get_parameters <name>     - モデルのparameters一覧を取得")

    print("クライアント制御コマンド (WebSocket経由):")
    print("  client <client_id> get_eye_blink")
    print("  client <client_id> set_eye_blink [enabled|disabled]")

    print("  client <client_id> get_breath")
    print("  client <client_id> set_breath [enabled|disabled]")

    print("  client <client_id> get_idle_motion")
    print("  client <client_id> set_idle_motion [enabled|disabled]")

    print("  client <client_id> get_drag_follow")
    print("  client <client_id> set_drag_follow [enabled|disabled]")

    print("  client <client_id> get_physics")
    print("  client <client_id> set_physics [enabled|disabled]")

    print("  client <client_id> get_expression")
    print("  client <client_id> set_expression [expression_name]")

    print("  client <client_id> get_motion")
    print("  client <client_id> set_motion [group_name] [no] [priority(0-3, default:2)]")

    print("  client <client_id> get_model")
    print("  client <client_id> set_parameter ID01=VALUE01 ID02=VALUE02 ...")
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

            parts = user_input.strip().split(maxsplit=2)
            command = parts[0].lower()

            if command == "quit":
                logger.info("サーバーを停止します...")
                break

            elif command == "send" and len(parts) > 1:
                # 形式: send <client_id> <message>
                if len(parts) < 3:
                    logger.warning("使い方: send <client_id> <message>")
                    continue

                target_client_id = parts[1]
                message = parts[2]

                success = await send_to_client(target_client_id, {
                    "type": "send",
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
                    "type": "notify",
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

            # elif command == "count":
            #    logger.info(f"接続数: {len(connected_clients)}")

            elif command == "model" and len(parts) > 1:
                sub_command = parts[1]
                args = parts[2] if len(parts) > 2 else ""
                await model_command(sub_command, args)

            elif command == "client" and len(parts) > 1:
                # 形式: client <client_id> <sub_command> [args...]
                if len(parts) < 3:
                    logger.warning(
                        "使い方: client <client_id> <command> [args...]")
                    continue
                cmd_parts = parts[2].split(maxsplit=1)
                sub_command = cmd_parts[0]
                target_client_id = parts[1]  # client_idを抽出
                args = {}
                if len(cmd_parts) > 1:
                    args = cmd_parts[1]

                response = await client_command(sub_command, args, target_client_id)
                logger.info(f"クライアントコマンド結果: {response}")

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
        default=os.environ.get('CUBISM_MODEL_DIR', 'src/Cubism/Resources'),
        help='モデルディレクトリのパス (デフォルト: src/Cubism/Resources, 環境変数: CUBISM_MODEL_DIR)'
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
    parser.add_argument(
        '--no-console',
        action='store_true',
        help='対話型コンソールを無効化（ログのみ出力）'
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

    host = args.host
    port = args.port

    logger.info(f"WebSocketサーバーを起動中: ws://{host}:{port}")

    async with websockets.serve(handle_client, host, port):
        # サーバーコンソールを起動（--no-console が指定されていない場合のみ）
        if not args.no_console:
            logger.info("サーバーが起動しました。Ctrl+Cで停止します。")
            console_task = asyncio.create_task(server_console())
            # コンソールタスクが終了するまで待機
            await console_task
        else:
            # コンソールなしモード：無限待機
            logger.info("サーバーが起動しました。コンソールなしで動作中")
            await asyncio.Future()  # 無限待機

        # オプション: 定期メッセージタスクをキャンセル
        # periodic_task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nサーバーを停止しました")
