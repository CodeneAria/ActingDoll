"""
WebSocket Server for bidirectional communication with MCP support
サーバー側のWebSocket通信アプリケーション（MCP対応）
"""
import asyncio
import json
import logging
import base64
from datetime import datetime
from typing import Set, Optional
import moc3manager
import websockets
from websockets.server import ServerConnection
from security_config import SecurityConfig

logger = logging.getLogger("WSS")
# ServerConnection（websockets）のログレベルをWARNINGに設定
logging.getLogger('websockets').setLevel(logging.WARNING)

task_cubism = None  # グローバルなMCPサーバーインスタンス


class CubismControllerHandler:
    """
    CubismControllerHandlerは、Cubism Controllerのクライアント接続を処理し、
    Live2Dモデルの制御コマンドを処理するクラスです。
    """

    # 接続されたクライアントを管理
    connected_clients: Set[ServerConnection] = set()
    # クライアントIDとWebSocket接続のマッピング
    client_id_map: dict[str, ServerConnection] = {}
    # 認証済みクライアントを追跡
    authenticated_clients: Set[ServerConnection] = set()
    # クライアントIDとクライアントタイプのマッピング
    client_type_map: dict[str, str] = {}

    # グローバルなモデルマネージャー（後で初期化）
    model_manager = None
    # グローバルなセキュリティ設定（後で初期化）
    security_config: Optional[SecurityConfig] = None

    # MCPサーバー停止関数のグローバル変数
    fnc_stop_mcp = None
    # サーバーの実行状態を管理
    is_running = False

    def print_server_console(self):
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
        print("  client <client_id> get_model_name")
        print("  client <client_id> get_model_info")

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
        print(
            "  client <client_id> set_motion [group_name] [no] [priority(0-3, default:2)]")

        print("  client <client_id> set_lipsync [base64_wav_data]")
        print("  client <client_id> set_lipsync_from_file [filename]")
        print("    ※ set_lipsync_from_fileは、auth コマンドで認証が必要")
        print("  client <client_id> set_parameter ID01=VALUE01 ID02=VALUE02 ...")

        print("  client <client_id> get_position")
        print("  client <client_id> set_position [x] [y] <relative>")

        print("  client <client_id> get_scale")
        print("  client <client_id> set_scale [size]")
        print("========================\n")

    async def broadcast_message(self, message: dict, exclude: ServerConnection = None):
        """
        全クライアントにメッセージをブロードキャスト

        Args:
            message: 送信するメッセージ（辞書形式）
            exclude: 除外するクライアント接続
        """
        if self.connected_clients:
            message_json = json.dumps(message, ensure_ascii=False)
            # 送信失敗したクライアントを追跡
            disconnected = set()

            for client in self.connected_clients:
                if client != exclude:
                    try:
                        await client.send(message_json)
                    except websockets.exceptions.ConnectionClosed:
                        disconnected.add(client)

            # 切断されたクライアントを削除
            self.connected_clients.difference_update(disconnected)

    async def send_to_client(self, client_id: str, message: dict) -> bool:
        """
        特定のクライアントにメッセージを送信

        Args:
            client_id: 送信先のクライアントID
            message: 送信するメッセージ（辞書形式）

        Returns:
            送信成功ならTrue、失敗ならFalse
        """
        if client_id not in self.client_id_map:
            logger.warning(f"クライアント {client_id} が見つかりません")
            return False

        websocket = self.client_id_map[client_id]
        message_json = json.dumps(message, ensure_ascii=False)

        try:
            await websocket.send(message_json)
            return True
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"クライアント {client_id} への送信に失敗（切断済み）")
            # クリーンアップ
            self.connected_clients.discard(websocket)
            self.client_id_map.pop(client_id, None)
            return False
        except Exception as e:
            logger.error(f"クライアント {client_id} への送信エラー: {e}")
            return False

    def get_client_id(self, websocket: ServerConnection) -> str:
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

    async def handle_client(self, websocket: ServerConnection):
        """
        クライアント接続を処理

        Args:
            websocket: WebSocket接続
        """
        # クライアントIDを生成
        client_id = self.get_client_id(websocket)
        logger.info(f"新しいクライアント接続: {client_id}")

        # クライアントを登録
        self.connected_clients.add(websocket)
        self.client_id_map[client_id] = websocket

        try:
            # ウェルカムメッセージを送信
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Welcome to the Cubism Controller!",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False))

            # メッセージ受信ループ
            async for message in websocket:
                try:
                    # JSON形式で受信
                    data = json.loads(message)
                    logger.debug(f"Received from {client_id}: {data}")

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

                    elif msg_type == "auth":
                        # 認証処理
                        token = data.get("token")
                        if self.security_config and self.security_config.validate_auth_token(token):
                            self.authenticated_clients.add(websocket)
                            await websocket.send(json.dumps({
                                "type": "auth_success",
                                "message": "Authentication successful",
                                "client_id": client_id
                            }, ensure_ascii=False))
                            logger.info(f"認証成功: {client_id}")
                        else:
                            await websocket.send(json.dumps({
                                "type": "auth_failed",
                                "message": "Authentication failed: Invalid token"
                            }, ensure_ascii=False))
                            logger.warning(f"認証失敗: {client_id}")

                    elif msg_type == "broadcast":
                        # 全クライアントにブロードキャスト
                        broadcast_data = {
                            "type": "broadcast_message",
                            "from": client_id,
                            "content": data.get("content"),
                            "timestamp": datetime.now().isoformat()
                        }
                        await self.broadcast_message(broadcast_data)

                    elif msg_type == "command":
                        # コマンド処理の例
                        command = data.get("command")
                        response = await self.process_command(command, client_id)
                        logger.debug(f"<command> {client_id}::{response}")
                        await websocket.send(json.dumps(response, ensure_ascii=False))

                    elif msg_type == "model":
                        # モデルコマンド処理
                        command = data.get("command")
                        args = data.get("args", "")
                        response = await self.model_command(command, args, client_id)
                        await websocket.send(json.dumps(response, ensure_ascii=False))

                    elif msg_type == "client":
                        # クライアント状態管理コマンド処理
                        command = data.get("command")
                        args = data.get("args", {})
                        source_client_id = data.get("from", "")
                        await self.client_command(command, args, client_id, source_client_id)
                        # await websocket.send(json.dumps(response, ensure_ascii=False))

                    else:
                        # その他のメッセージは全クライアントに転送
                        forward_data = {
                            "type": "message",
                            "from": client_id,
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        }
                        await self.broadcast_message(forward_data, exclude=websocket)

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
            logger.debug(f"クリーンアップ処理: {client_id}")
            # クライアントを削除
            self.connected_clients.discard(websocket)
            self.authenticated_clients.discard(websocket)
            self.client_id_map.pop(client_id, None)
            self.client_type_map.pop(client_id, None)

            # 切断通知をブロードキャスト
            await self.broadcast_message({
                "type": "client_disconnected",
                "timestamp": datetime.now().isoformat(),
                "total_clients": len(self.connected_clients)
            })

    async def model_command(self, command: str, args: str, client_id: str) -> dict:
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
            models = self.model_manager.get_models()
            logger.debug(f"利用可能なモデル: {models}")
            return {
                "type": "command_response",
                "command": "model",
                "sub": command,
                "from": client_id,
                "data": models
            }

        # 2. model get_expressions <model_name> - モデルのexpressionsを取得
        elif command == "get_expressions":
            if not args:
                return {
                    "type": "command_response",
                    "command": "model",
                    "sub": command,
                    "from": client_id,
                    "error": "モデル名が必要です"
                }
            model_info = self.model_manager.get_model_info(args)
            if model_info:
                expressions = model_info.get(
                    'FileReferences', {}).get('Expressions', [])
                expression_names = [exp.get('Name') for exp in expressions]
                logger.info(f"expressions一覧: {expression_names}")
                return {
                    "type": "command_response",
                    "command": "model",
                    "sub": command,
                    "from": client_id,
                    "data": {
                        "model_name": args,
                        "expressions": expressions
                    }
                }
            return {
                "type": "command_response",
                "command": "model",
                "sub": command,
                "from": client_id,
                "error": f"モデル '{args}' が見つかりません"
            }

        # 3. model get_motions <model_name> - モデルのmotionsを取得
        elif command == "get_motions":
            if not args:
                return {
                    "type": "command_response",
                    "command": "model",
                    "sub": command,
                    "from": client_id,
                    "error": "モデル名が必要です"
                }
            model_info = self.model_manager.get_model_info(args)
            if model_info:
                motions = model_info.get(
                    'FileReferences', {}).get('Motions', {})
                motion_summary = {}
                for group_name, motion_list in motions.items():
                    motion_summary[group_name] = [
                        m.get('File') for m in motion_list]
                logger.info(f"motions一覧: {motion_summary}")
                return {
                    "type": "command_response",
                    "command": "model",
                    "sub": command,
                    "from": client_id,
                    "data": {
                        "model_name": args,
                        "motions": motions
                    }
                }
            return {
                "type": "command_response",
                "command": "model",
                "sub": command,
                "from": client_id,
                "error": f"モデル '{args}' が見つかりません"
            }

        # 4. model get_parameters <model_name> - モデルのparametersを取得
        elif command == "get_parameters":
            if not args:
                return {
                    "type": "command_response",
                    "command": "model",
                    "sub": command,
                    "from": client_id,
                    "error": "モデル名が必要です"
                }
            parameters = self.model_manager.get_parameters_exclude_physics(
                args)
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
                    "command": "model",
                    "sub": command,
                    "from": client_id,
                    "data": {
                        "model_name": args,
                        "parameters": param_summary
                    }
                }
            return {
                "type": "command_response",
                "command": "model",
                "sub": command,
                "from": client_id,
                "data": {
                    "model_name": args,
                    "parameters": []
                }
            }

        else:
            return {
                "type": "command_response",
                "command": "model",
                "sub": command,
                "from": client_id,
                "error": f"不明なコマンド: {command}"
            }

    async def client_command(self, command: str, args: dict,
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
        if client_id not in self.client_id_map:
            return {
                "type": "client",
                "command": command,
                "from": source_client_id,
                "error": f"クライアント '{client_id}' が見つかりません"
            }

        if command.startswith("response_"):
            if ("" != source_client_id) and (client_id != source_client_id):
                if (source_client_id in self.client_id_map):
                    await self.send_to_client(source_client_id, {
                        "type": "command_response",
                        "command": command,
                        "client_id": client_id,
                        "data": args,
                        "timestamp": datetime.now().isoformat()
                    })
            return {
                "type": "client_response",
                "command": command,
                "success": True,
                "client_id": client_id,
                "from": source_client_id,
                "data": args,
                "message": "クライアントからレスポンスを受信しました"
            }

        elif command.startswith("thanks"):
            self.client_type_map[client_id] = args.get(
                "client_type", "unknown")
            logger.debug(
                f"{client_id}を{self.client_type_map[client_id]}として登録")
            pass
        elif command.startswith("set_"):
            if command == "set_eye_blink":  # アニメーション設定 - 自動目パチ
                if not args:
                    return {
                        "type": "client",
                        "command": command,
                        "from": source_client_id,
                        "error": "パラメータを指定してください: enabled or disabled"
                    }
                if isinstance(args, dict):
                    enabled = args.get("enabled", True)
                else:
                    enabled = ("enabled" in str(args).lower())
                await self.send_to_client(client_id, {
                    "type": "set_eye_blink",
                    "client_id": client_id,
                    "from": source_client_id,
                    "enabled": enabled,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "set_eye_blink",
                    "success": True,
                    "from": source_client_id,
                    "data": {"enabled": enabled},
                    "message": "クライアントに自動目パチ設定を送信しました"
                }

            elif command == "set_breath":  # アニメーション設定 - 呼吸
                if not args:
                    return {
                        "type": "client",
                        "command": command,
                        "from": source_client_id,
                        "error": "パラメータを指定してください: enabled or disabled"
                    }
                if isinstance(args, dict):
                    enabled = args.get("enabled", True)
                else:
                    enabled = ("enabled" in str(args).lower())
                await self.send_to_client(client_id, {
                    "type": "set_breath",
                    "client_id": client_id,
                    "from": source_client_id,
                    "enabled": enabled,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "set_breath",
                    "success": True,
                    "from": source_client_id,
                    "data": {"enabled": enabled},
                    "message": "クライアントに呼吸設定を送信しました"
                }

            elif command == "set_idle_motion":  # アニメーション設定 - アイドリングモーション
                if not args:
                    return {
                        "type": "client",
                        "command": command,
                        "from": source_client_id,
                        "error": "パラメータを指定してください: enabled or disabled"
                    }
                if isinstance(args, dict):
                    enabled = args.get("enabled", True)
                else:
                    enabled = ("enabled" in str(args).lower())
                await self.send_to_client(client_id, {
                    "type": "set_idle_motion",
                    "client_id": client_id,
                    "from": source_client_id,
                    "enabled": enabled,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "set_idle_motion",
                    "success": True,
                    "from": source_client_id,
                    "data": {"enabled": enabled},
                    "message": "クライアントにアイドリングモーション設定を送信しました"
                }

            elif command == "set_drag_follow":  # アニメーション設定 - ドラッグ追従
                if not args:
                    return {
                        "type": "client",
                        "command": command,
                        "from": source_client_id,
                        "error": "パラメータを指定してください: enabled or disabled"
                    }
                if isinstance(args, dict):
                    enabled = args.get("enabled", True)
                else:
                    enabled = ("enabled" in str(args).lower())
                await self.send_to_client(client_id, {
                    "type": "set_drag_follow",
                    "client_id": client_id,
                    "from": source_client_id,
                    "enabled": enabled,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "set_drag_follow",
                    "success": True,
                    "from": source_client_id,
                    "data": {"enabled": enabled},
                    "message": "クライアントにドラッグ追従設定を送信しました"
                }

            elif command == "set_physics":  # アニメーション設定 - 物理演算
                if not args:
                    return {
                        "type": "client",
                        "command": command,
                        "from": source_client_id,
                        "error": "パラメータを指定してください: enabled or disabled"
                    }
                if isinstance(args, dict):
                    enabled = args.get("enabled", True)
                else:
                    enabled = ("enabled" in str(args).lower())
                await self.send_to_client(client_id, {
                    "type": "set_physics",
                    "client_id": client_id,
                    "from": source_client_id,
                    "enabled": enabled,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "set_physics",
                    "success": True,
                    "from": source_client_id,
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
                        "from": source_client_id,
                        "error": "expression名が必要です"
                    }
                await self.send_to_client(client_id, {
                    "type": "set_expression",
                    "client_id": client_id,
                    "from": source_client_id,
                    "expression": expression,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "set_expression",
                    "success": True,
                    "from": source_client_id,
                    "data": {"client_id": client_id, "expression": expression},
                    "message": "クライアントに表情設定を送信しました"
                }

            elif command == "set_motion":  # Motions
                parts = args.strip().split(maxsplit=2) if len(args) > 0 else ""
                group = parts[0] if len(parts) > 0 else ""
                no = parts[1] if len(parts) > 1 else ""
                # デフォルトはPriorityNormal(2)
                priority = parts[2] if len(parts) > 2 else "2"

                if not group:
                    return {
                        "type": "client_request",
                        "command": "set_motion",
                        "from": source_client_id,
                        "error": "motion group名が必要です"
                    }
                if not no:
                    return {
                        "type": "client_request",
                        "command": "set_motion",
                        "from": source_client_id,
                        "error": "motion noが必要です"
                    }

                # priorityを整数に変換
                try:
                    priority_int = int(priority)
                    if priority_int < 0 or priority_int > 3:
                        return {
                            "type": "client_request",
                            "command": "set_motion",
                            "from": source_client_id,
                            "error": "priorityは0(None), 1(Idle), 2(Normal), 3(Force)のいずれかである必要があります"
                        }
                except ValueError:
                    return {
                        "type": "client_request",
                        "command": "set_motion",
                        "from": source_client_id,
                        "error": "priorityは整数である必要があります"
                    }

                await self.send_to_client(client_id, {
                    "type": "set_motion",
                    "client_id": client_id,
                    "from": source_client_id,
                    "group": group,
                    "no": no,
                    "priority": priority_int,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "set_motion",
                    "success": True,
                    "from": source_client_id,
                    "data": {"group": group, "no": no, "priority": priority_int},
                    "message": "クライアントにモーション情報を送信しました"
                }

            elif command == "set_lipsync":  # リップシンク用Wavファイル送信
                parts = args.strip().split(maxsplit=1) if len(args) > 0 else []
                wav_data = parts[0] if len(parts) > 0 else ""

                if not wav_data:
                    return {
                        "type": "client_request",
                        "command": "set_lipsync",
                        "from": source_client_id,
                        "error": "Wavデータが必要です"
                    }

                await self.send_to_client(client_id, {
                    "type": "set_lipsync",
                    "client_id": client_id,
                    "from": source_client_id,
                    "wav_data": wav_data,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "set_lipsync",
                    "success": True,
                    "from": source_client_id,
                    "message": "クライアントにWavファイルを送信しました"
                }
            elif command == "set_lipsync_from_file":  # リップシンク用Wavファイル送信
                # 認証チェック: このコマンドは認証が必要
                source_ws = self.client_id_map.get(source_client_id)
                if self.security_config and self.security_config.require_auth:
                    if not source_ws or source_ws not in self.authenticated_clients:
                        logger.warning(
                            f"認証されていないクライアントがset_lipsync_from_fileを試行: {source_client_id}")
                        return {
                            "type": "client_request",
                            "command": "set_lipsync_from_file",
                            "from": source_client_id,
                            "error": "このコマンドには認証が必要です。先にauthコマンドで認証してください。"
                        }

                parts = args.strip().split(maxsplit=1) if len(args) > 0 else []
                file_name = parts[0] if len(parts) > 0 else ""

                if not file_name:
                    return {
                        "type": "client_request",
                        "command": "set_lipsync_from_file",
                        "from": source_client_id,
                        "error": "Wavファイル名が必要です"
                    }

                # セキュリティチェック: ファイルパスがホワイトリストに含まれているか確認
                if self.security_config and not self.security_config.is_file_allowed(file_name):
                    logger.warning(
                        f"ファイルアクセス拒否: {file_name} (クライアント: {source_client_id})")
                    return {
                        "type": "client_request",
                        "command": "set_lipsync_from_file",
                        "from": source_client_id,
                        "error": f"ファイル '{file_name}' へのアクセスが拒否されました。許可されたディレクトリ内のファイルのみアクセス可能です。"
                    }

                wav_data = ""
                try:
                    with open(file_name, 'rb') as f:
                        data = f.read()
                        wav_data = base64.b64encode(data).decode('utf-8')
                except FileNotFoundError:
                    return {
                        "type": "client_request",
                        "command": "set_lipsync_from_file",
                        "from": source_client_id,
                        "error": f"Wavファイル '{file_name}' が見つかりません"
                    }
                except PermissionError:
                    return {
                        "type": "client_request",
                        "command": "set_lipsync_from_file",
                        "from": source_client_id,
                        "error": f"Wavファイル '{file_name}' へのアクセス権限がありません"
                    }
                except Exception as e:
                    logger.error(f"ファイル読み込みエラー: {e}")
                    return {
                        "type": "client_request",
                        "command": "set_lipsync_from_file",
                        "from": source_client_id,
                        "error": f"Wavファイル '{file_name}' の読み込みに失敗しました"
                    }

                if not wav_data:
                    return {
                        "type": "client_request",
                        "command": "set_lipsync_from_file",
                        "from": source_client_id,
                        "error": f"Wavファイル '{file_name}' の読み込みに失敗しました"
                    }

                await self.send_to_client(client_id, {
                    "type": "set_lipsync",
                    "client_id": client_id,
                    "from": source_client_id,
                    "wav_data": wav_data,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "set_lipsync",
                    "success": True,
                    "from": source_client_id,
                    "message": "クライアントにWavファイルを送信しました"
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
                            "from": source_client_id,
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
                            "from": source_client_id,
                            "error": f"パラメータの解析に失敗しました: {str(e)}"
                        }
                else:
                    return {
                        "type": "client",
                        "command": command,
                        "from": source_client_id,
                        "error": "パラメータは辞書形式または 'ParamName=value' 形式で指定してください"
                    }

                if not parameters:
                    return {
                        "type": "client",
                        "command": command,
                        "from": source_client_id,
                        "error": "有効なパラメータが指定されていません"
                    }

                # クライアントにパラメータ設定を送信
                success = await self.send_to_client(client_id, {
                    "type": "set_parameter",
                    "client_id": client_id,
                    "from": source_client_id,
                    "parameters": parameters,
                    "timestamp": datetime.now().isoformat()
                })

                if success:
                    return {
                        "type": "client",
                        "command": command,
                        "success": True,
                        "from": source_client_id,
                        "client_id": client_id,
                        "parameters": parameters,
                        "message": f"パラメータ設定コマンドを送信しました（{len(parameters)}個）"
                    }
                else:
                    return {
                        "type": "client",
                        "command": command,
                        "from": source_client_id,
                        "error": f"パラメータ設定の送信に失敗しました"
                    }

            elif command == "set_position":  # モデル位置設定
                parts = args.strip().split() if len(args) > 0 else []
                if len(parts) < 2:
                    return {
                        "type": "client_request",
                        "command": "set_position",
                        "from": source_client_id,
                        "error": "x座標とy座標が必要です: set_position [x] [y] <relative>"
                    }

                try:
                    x = float(parts[0])
                    y = float(parts[1])
                    relative = parts[2].lower() == "relative" if len(
                        parts) > 2 else False
                except ValueError:
                    return {
                        "type": "client_request",
                        "command": "set_position",
                        "from": source_client_id,
                        "error": "x座標とy座標は数値である必要があります"
                    }

                await self.send_to_client(client_id, {
                    "type": "set_position",
                    "client_id": client_id,
                    "from": source_client_id,
                    "x": x,
                    "y": y,
                    "relative": relative,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "set_position",
                    "success": True,
                    "from": source_client_id,
                    "data": {"x": x, "y": y, "relative": relative},
                    "message": f"クライアントに位置設定を送信しました (x={x}, y={y}, relative={relative})"
                }

            elif command == "set_scale":  # モデルスケール設定
                parts = args.strip().split() if len(args) > 0 else []
                if not parts:
                    return {
                        "type": "client_request",
                        "command": "set_scale",
                        "from": source_client_id,
                        "error": "スケール値が必要です: set_scale [size]"
                    }

                try:
                    scale = float(parts[0])
                except ValueError:
                    return {
                        "type": "client_request",
                        "command": "set_scale",
                        "from": source_client_id,
                        "error": "スケール値は数値である必要があります"
                    }

                await self.send_to_client(client_id, {
                    "type": "set_scale",
                    "client_id": client_id,
                    "from": source_client_id,
                    "scale": scale,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "set_scale",
                    "success": True,
                    "from": source_client_id,
                    "data": {"scale": scale},
                    "message": f"クライアントにスケール設定を送信しました (scale={scale})"
                }

        elif command.startswith("get_"):
            if command == "get_eye_blink":  # アニメーション設定 - 自動目パチ
                await self.send_to_client(client_id, {
                    "type": "request_eye_blink",
                    "from": source_client_id,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "get_eye_blink",
                    "from": source_client_id,
                    "client_id": client_id,
                    "message": "クライアントに自動目パチ設定をリクエストしました"
                }

            elif command == "get_breath":  # アニメーション設定 - 呼吸
                await self.send_to_client(client_id, {
                    "type": "request_breath",
                    "from": source_client_id,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "get_breath",
                    "from": source_client_id,
                    "client_id": client_id,
                    "message": "クライアントに呼吸設定をリクエストしました"
                }

            elif command == "get_idle_motion":  # アニメーション設定 - アイドリングモーション
                await self.send_to_client(client_id, {
                    "type": "request_idle_motion",
                    "from": source_client_id,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "get_idle_motion",
                    "from": source_client_id,
                    "client_id": client_id,
                    "message": "クライアントにアイドリングモーション設定をリクエストしました"
                }

            elif command == "get_drag_follow":  # アニメーション設定 - ドラッグ追従
                await self.send_to_client(client_id, {
                    "type": "request_drag_follow",
                    "from": source_client_id,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "get_drag_follow",
                    "from": source_client_id,
                    "client_id": client_id,
                    "message": "クライアントにドラッグ追従設定をリクエストしました"
                }

            elif command == "get_physics":  # アニメーション設定 - 物理演算
                await self.send_to_client(client_id, {
                    "type": "request_physics",
                    "from": source_client_id,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "get_physics",
                    "from": source_client_id,
                    "client_id": client_id,
                    "message": "クライアントに物理演算設定をリクエストしました"
                }

            elif command == "get_expression":  # Expressions
                await self.send_to_client(client_id, {
                    "type": "request_expression",
                    "from": source_client_id,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "get_expression",
                    "from": source_client_id,
                    "client_id": client_id,
                    "message": "クライアントに表情設定をリクエストしました"
                }

            elif command == "get_motion":  # Motions
                await self.send_to_client(client_id, {
                    "type": "request_motion",
                    "from": source_client_id,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "get_motion",
                    "from": source_client_id,
                    "client_id": client_id,
                    "message": "クライアントにモーション情報をリクエストしました"
                }

            elif command == "get_model_name":  # クライアントにモデル情報要求を送信
                await self.send_to_client(client_id, {
                    "type": "request_model_name",
                    "from": source_client_id,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "get_model_name",
                    "success": True,
                    "from": source_client_id,
                    "client_id": client_id,
                    "message": "クライアントにモデル情報をリクエストしました"
                }
            elif command == "get_model_info":  # クライアントにモデル情報要求を送信
                await self.send_to_client(client_id, {
                    "type": "request_model_info",
                    "from": source_client_id,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "get_model_info",
                    "success": True,
                    "from": source_client_id,
                    "client_id": client_id,
                    "message": "クライアントにモデル情報をリクエストしました"
                }

            elif command == "get_position":  # モデル位置取得
                await self.send_to_client(client_id, {
                    "type": "request_position",
                    "from": source_client_id,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "get_position",
                    "success": True,
                    "from": source_client_id,
                    "client_id": client_id,
                    "message": "クライアントに位置取得リクエストを送信しました"
                }

            elif command == "get_scale":  # モデルスケール取得
                await self.send_to_client(client_id, {
                    "type": "request_scale",
                    "from": source_client_id,
                    "timestamp": datetime.now().isoformat()
                })
                return {
                    "type": "client_request",
                    "command": "get_scale",
                    "success": True,
                    "from": source_client_id,
                    "client_id": client_id,
                    "message": "クライアントにスケール取得リクエストを送信しました"
                }

        return {
            "type": "client",
            "command": command,
            "from": source_client_id,
            "error": f"不明なクライアントコマンド: {command}"
        }

    async def process_command(self, user_input: str, client_id: str) -> dict:
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
                "from": client_id,
                "data": {
                    "connected_clients": len(self.connected_clients),
                    "server_time": datetime.now().isoformat()
                }
            }
        elif command == "auth":
            # 認証コマンド処理
            if len(parts) < 2:
                return {
                    "type": "command_response",
                    "command": "auth",
                    "from": client_id,
                    "error": "使い方: auth <token>"
                }

            token = parts[1]
            websocket = self.client_id_map.get(client_id)

            if self.security_config and self.security_config.validate_auth_token(token):
                if websocket:
                    self.authenticated_clients.add(websocket)
                return {
                    "type": "command_response",
                    "command": "auth",
                    "from": client_id,
                    "success": True,
                    "message": "認証に成功しました"
                }
            else:
                return {
                    "type": "command_response",
                    "command": "auth",
                    "from": client_id,
                    "success": False,
                    "error": "認証に失敗しました: 無効なトークン"
                }
        elif command == "ping":
            return {
                "type": "command_response",
                "command": "ping",
                "from": client_id,
                "data": "pong"
            }
        elif command == "list":
            json_data = {}
            if self.client_id_map:
                # コマンド送信者自身を除外したクライアントリストを作成
                other_clients = [
                    cid for cid in self.client_id_map.keys() if (cid != client_id) and (self.client_type_map.get(cid, "API") == 'ActorDoll')
                ]
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
                "from": client_id,
                "data": json_data
            }
        elif command == "notify":
            message = parts[1]
            await self.broadcast_message({
                "type": "notify",
                "message": message,
                "from": client_id,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "command_response",
                "command": command,
                "from": client_id,
                "data": message
            }
        elif command == "send":
            args = parts[1].strip().split(maxsplit=2)
            # 形式: send <client_id> <message>
            if len(args) < 2:
                return {
                    "type": "command_response",
                    "command": command,
                    "from": client_id,
                    "error": "使い方: send <client_id> <message>"
                }

            target_client_id = args[0]
            message = args[1]

            success = await self.send_to_client(target_client_id, {
                "type": "send",
                "from": client_id,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            return {
                "type": "command_response",
                "command": command,
                "from": client_id,
                "success": True if success else False
            }
        elif command == "model":
            # モデルコマンドを処理
            # 形式: model <sub_command> [args]
            if len(parts) < 2:
                return {
                    "type": "command_response",
                    "command": command,
                    "from": client_id,
                    "error": "使い方: model <sub_command> [args]"
                }

            # サブコマンドと引数を分離
            sub_parts = parts[1].strip().split(maxsplit=1)
            sub_command = sub_parts[0].lower()
            args = sub_parts[1] if len(sub_parts) > 1 else ""

            # model_command関数を呼び出し
            return await self.model_command(sub_command, args, client_id)

        elif command == "client":
            # クライアント制御コマンドを処理
            # 形式: client <client_id> <sub_command> [args]
            if len(parts) < 2:
                return {
                    "type": "command_response",
                    "command": command,
                    "from": client_id,
                    "error": "使い方: client <client_id> <sub_command> [args]"
                }

            # client_id、サブコマンド、引数を分離
            client_parts = parts[1].strip().split(maxsplit=2)
            if len(client_parts) < 2:
                return {
                    "type": "command_response",
                    "command": command,
                    "from": client_id,
                    "error": "使い方: client <client_id> <sub_command> [args]"
                }

            target_client_id = client_parts[0]
            sub_command = client_parts[1].lower()
            args = client_parts[2] if len(client_parts) > 2 else ""

            # client_command関数を呼び出し
            return await self.client_command(sub_command, args, target_client_id, client_id)

        else:
            return {
                "type": "command_response",
                "command": command,
                "from": client_id,
                "error": "不明なコマンドです"
            }

    async def server_console(self):
        """
        サーバーコンソール - サーバーから能動的にメッセージを送信
        """
        self.print_server_console()

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
                    # MCPサーバーを停止
                    try:
                        if self.fnc_stop_mcp:
                            await self.fnc_stop_mcp()
                    except Exception as e:
                        logger.error(f"MCPサーバー停止中にエラーが発生しました: {e}")
                    break

                elif command == "send" and len(parts) > 1:
                    # 形式: send <client_id> <message>
                    if len(parts) < 3:
                        logger.warning("使い方: send <client_id> <message>")
                        continue

                    target_client_id = parts[1]
                    message = parts[2]

                    success = await self.send_to_client(target_client_id, {
                        "type": "send",
                        "message": message,
                        "timestamp": datetime.now().isoformat()
                    })
                    if success:
                        logger.info(
                            f"メッセージ送信完了 -> {target_client_id}: {message}")
                    else:
                        logger.error(f"メッセージ送信失敗 -> {target_client_id}")

                elif command == "notify" and len(parts) > 1:
                    message = parts[1]
                    await self.broadcast_message({
                        "type": "notify",
                        "message": message,
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.info(f"通知送信: {message}")

                elif command == "list":
                    if self.client_id_map:
                        logger.info(
                            f"接続中のクライアント ({len(self.client_id_map)}件):")
                        for i, client_id in enumerate(self.client_id_map.keys(), 1):
                            logger.info(f"  {i}. {client_id}")
                    else:
                        logger.info("接続中のクライアントはありません")

                # elif command == "count":
                #    logger.info(f"接続数: {len(connected_clients)}")

                elif command == "model" and len(parts) > 1:
                    sub_command = parts[1]
                    args = parts[2] if len(parts) > 2 else ""
                    await self.model_command(sub_command, args, "SERVER")

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

                    response = await self.client_command(sub_command, args, target_client_id)
                    logger.info(f"クライアントコマンド結果: {response}")

                else:
                    logger.warning(f"不明なコマンド: {command}")
                    self.print_server_console()

            except EOFError:
                break
            except Exception as e:
                logger.error(f"コンソールエラー: {e}")

    async def send_periodic_messages(self):
        """
        定期的なメッセージ送信（オプション）
        必要に応じて有効化
        """
        while self.is_running:
            await asyncio.sleep(1)
            # await asyncio.sleep(60)  # 60秒ごと
            # if self.connected_clients:
            #    await self.broadcast_message({
            # "type": "server_heartbeat",
            #        "message": "サーバーは正常に動作中",
            #        "timestamp": datetime.now().isoformat(),
            #        "connected_clients": len(self.connected_clients)
            #    })

    async def run(self,
                  host: str, port: int,
                  security: SecurityConfig,
                  stop_mcp_server: any,
                  model_dir: str,
                  no_console: bool = False,
                  disable_auth: bool = False):
        """
        Cubism Controllerを起動

        Args:
            host: バインドするホストアドレス
            port: バインドするポート
            security: セキュリティ設定
            stop_mcp_server: MCPサーバー停止関数
            model_dir: モデルディレクトリパス
            no_console: コンソール無効化フラグ
            disable_auth: 認証無効化フラグ
        """

        # セキュリティ設定を初期化
        self.security_config = security
        self.fnc_stop_mcp = stop_mcp_server

        # モデルマネージャーを初期化
        self.model_manager = moc3manager.ModelManager(model_dir)

        # セキュリティ情報をログ出力
        if self.security_config.require_auth and not disable_auth:
            if self.security_config.auth_token:
                logger.info("トークン認証が有効です")
            else:
                logger.warning("警告: 認証が必須ですが、WEBSOCKET_AUTH_TOKENが設定されていません。"
                               "接続は全て拒否されます")
        else:
            logger.warning("警告: 認証が無効です。"
                           "本番環境では認証を有効にすることを推奨します")

        if self.security_config.allowed_file_dirs:
            logger.info(
                f"アクセスホワイトリスト: {[str(d) for d in self.security_config.allowed_file_dirs]}")
        else:
            logger.info("アクセスホワイトリスト: 未設定（ファイル読み取りコマンド無効）")

        try:
            async with websockets.serve(self.handle_client, host, port):
                self.is_running = True
                if not no_console:
                    await asyncio.sleep(1.5)  # サーバーが起動するまでしばらく待機
                    logger.info("Cubism Controllerが起動しました: "
                                f"ws://{host}:{port}")
                    await self.server_console()
                else:
                    logger.info("Cubism Controllerが起動しました"
                                "（コンソールなし）: "
                                f"ws://{host}:{port}")
                    await self.send_periodic_messages()
        except Exception as e:
            logger.error(f"Cubism Controllerエラー: {e}")

    async def stop(self):
        """
        サーバー停止処理
        """
        logger.info("MCPサーバーを停止中...")
        # クライアントにサーバー停止通知を送信
        await self.broadcast_message({
            "type": "server_shutdown",
            "message": "サーバーは停止します",
            "timestamp": datetime.now().isoformat()
        })
        self.is_running = False
        # クライアント接続を全て閉じる
        for websocket in self.connected_clients:
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"クライアント接続のクローズ中にエラーが発生しました: {e}")
        self.connected_clients.clear()
        self.client_id_map.clear()
        self.authenticated_clients.clear()
        logger.info("MCPサーバーは正常に停止しました")


async def run_websocket(host: str, port: int,
                        security: SecurityConfig,
                        stop_mcp_server: any,
                        model_dir: str,
                        no_console: bool = False,
                        disable_auth: bool = False):
    """
    Cubism Controllerを起動

    Args:
        host: バインドするホストアドレス
        port: バインドするポート
        security: セキュリティ設定
        stop_mcp_server: MCPサーバー停止関数
        model_dir: モデルディレクトリパス
        no_console: コンソール無効化フラグ
        disable_auth: 認証無効化フラグ
    """
    global task_cubism

    task_cubism = CubismControllerHandler()

    try:
        await task_cubism.run(host=host, port=port,
                              security=security,
                              stop_mcp_server=stop_mcp_server,
                              model_dir=model_dir,
                              no_console=no_console,
                              disable_auth=disable_auth)
    except asyncio.CancelledError:
        logger.info("Cubism Controllerを停止中...")
        await task_cubism.stop()
    except Exception as e:
        logger.error(f"Cubism Controllerエラー: {e}")
