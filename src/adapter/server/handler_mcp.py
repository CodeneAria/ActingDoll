"""
MCP Server Handler for unified server
MCPサーバーハンドラー
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any
import websockets

# MCP imports
try:
    import uvicorn
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.server.sse import SseServerTransport
    from mcp.types import TextContent, Tool
    from starlette.requests import Request
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

logger = logging.getLogger("MCPHandler")
logger.setLevel(logging.INFO)

mcp_server = None  # グローバルなMCPサーバーインスタンス


class MCPHandler:
    """MCP handler"""

    def __init__(self):
        """Initialize MCP server
        """
        if not MCP_AVAILABLE:
            raise RuntimeError("MCPモジュールがインストールされていません")

        self.server = Server("acting-doll")
        self.websocket = None
        self.uvicorn_server = None
        self._setup_handlers()

    def _setup_handlers(self):
        """MCPサーバーのハンドラーを設定"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """利用可能なツール一覧を返す"""
            return [
                Tool(
                    # list
                    name="list_clients",
                    description="接続中のクライアント一覧を取得します",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    # model list
                    name="get_model_list",
                    description="利用可能なLive2Dモデルの一覧を取得します",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    # model get_expressions <name>
                    # model get_motions <name>
                    # model get_parameters <name>
                    name="get_model_info",
                    description="指定したモデルの詳細情報（expressions、motions、parameters）を取得します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "model_name": {"type": "string", "description": "モデル名"},
                        },
                        "required": ["model_name"],
                    },
                ),
                Tool(
                    # client <client_id> set_expression [expression_name]
                    name="set_expression",
                    description="クライアントのモデルの表情を設定します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "クライアントID（例: 127.0.0.1:12345）"},
                            "expression": {"type": "string", "description": "表情名"},
                        },
                        "required": ["client_id", "expression"],
                    },
                ),
                Tool(
                    # client <client_id> set_motion [group_name] [no] [priority(0-3, default:2)]
                    name="set_motion",
                    description="クライアントのモデルのモーションを再生します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "クライアントID"},
                            "group": {"type": "string", "description": "モーショングループ名"},
                            "no": {"type": "integer", "description": "モーション番号"},
                            "priority": {"type": "integer", "description": "優先度（0-3、デフォルト: 2）", "default": 2},
                        },
                        "required": ["client_id", "group", "no"],
                    },
                ),
                Tool(
                    # client <client_id> set_parameter ID01=VALUE01 ID02=VALUE02 ...
                    name="set_parameter",
                    description="クライアントのモデルのパラメータを設定します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "クライアントID"},
                            "parameters": {
                                "type": "object",
                                "description": "パラメータの辞書（例: {'ParamAngleX': 10.0}）",
                                "additionalProperties": {"type": "number"},
                            },
                        },
                        "required": ["client_id", "parameters"],
                    },
                ),
                Tool(
                    # client <client_id> set_eye_blink [enabled|disabled]
                    name="set_eye_blink",
                    description="まばたき機能の有効/無効を設定します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "クライアントID"},
                            "enabled": {"type": "boolean", "description": "有効化する場合はtrue"},
                        },
                        "required": ["client_id", "enabled"],
                    },
                ),
                Tool(
                    # client <client_id> set_breath [enabled|disabled]
                    name="set_breath",
                    description="呼吸エフェクトの有効/無効を設定します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "クライアントID"},
                            "enabled": {"type": "boolean", "description": "有効化する場合はtrue"},
                        },
                        "required": ["client_id", "enabled"],
                    },
                ),
                Tool(
                    # client <client_id> get_model
                    # client <client_id> get_expression
                    # client <client_id> get_motion
                    # client <client_id> get_eye_blink
                    # client <client_id> get_breath
                    # client <client_id> get_idle_motion
                    # client <client_id> get_drag_follow
                    # client <client_id> get_physics
                    # client <client_id> get_position
                    # client <client_id> get_scale
                    name="get_client_state",
                    description="クライアントの現在の状態（モデル、表情、モーション等）を取得します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "client_id": {"type": "string", "description": "クライアントID"},
                        },
                        "required": ["client_id"],
                    },
                ),
                Tool(
                    # notify <message>
                    name="notify",
                    description="状態を通知します",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "description": "通知メッセージ"},
                        },
                        "required": ["message"],
                    },
                )
                # send <client_id> <message>
                #
                # client <client_id> set_idle_motion [enabled|disabled]
                # client <client_id> set_physics [enabled|disabled]
                # client <client_id> set_lipsync [base64_wav_data]
                # client <client_id> set_lipsync_from_file [filename]
                # client <client_id> set_position [x] [y] <relative>
                # client <client_id> set_scale [size]
                # client <client_id> set_drag_follow [enabled|disabled]
                #
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """ツールを実行"""
            try:
                result = await self._handle_tool_call(name, arguments)
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]

    async def _handle_tool_call(self, name: str, arguments: dict) -> dict:
        """ツール呼び出しを処理"""
        if name == "get_model_list":
            return await self._get_model_list()
        elif name == "get_model_info":
            return await self._get_model_info(arguments["model_name"])
        elif name == "set_expression":
            return await self._set_expression(arguments["client_id"], arguments["expression"])
        elif name == "set_motion":
            return await self._set_motion(
                arguments["client_id"], arguments["group"],
                arguments["no"], arguments.get("priority", 2)
            )
        elif name == "set_parameter":
            return await self._set_parameter(arguments["client_id"], arguments["parameters"])
        elif name == "list_clients":
            return await self._list_clients()
        elif name == "get_client_state":
            return await self._get_client_state(arguments["client_id"])
        elif name == "set_eye_blink":
            return await self._set_eye_blink(arguments["client_id"], arguments["enabled"])
        elif name == "set_breath":
            return await self._set_breath(arguments["client_id"], arguments["enabled"])
        elif name == "notify":
            return await self._notify(arguments["message"])
        else:
            return {"error": f"Unknown tool: {name}"}

    async def _send_command(self, message: dict) -> dict:
        """
        WebSocketでコマンドを送信してレスポンスを受け取る
        Args:
            message: 送信するメッセージ（辞書形式）
        Returns:
            レスポンス（辞書形式）
        """
        try:
            if not self.websocket:
                return {"error": "WebSocket接続がありません"}

            # メッセージを送信
            await self.websocket.send(json.dumps(message, ensure_ascii=False))

            # レスポンスを受信
            response_text = await self.websocket.recv()
            response = json.loads(response_text)
            return response
        except Exception as e:
            logger.error(f"WebSocketコマンド送信エラー: {e}")
            return {"error": str(e)}

    async def _send_notify(self, message: dict):
        """
        WebSocketで通知メッセージを送信
        Args:
            message: 送信するメッセージ（辞書形式）
        """
        try:
            if not self.websocket:
                return {"error": "WebSocket接続がありません"}

            # メッセージを送信
            await self.websocket.send(json.dumps(message, ensure_ascii=False))

        except Exception as e:
            logger.error(f"WebSocketコマンド送信エラー: {e}")

    async def _send_thank_you_message(self, client_id: str):
        """クライアントに感謝のメッセージを送信"""
        if client_id != "unknown":
            await self._send_notify({
                'type': 'client',
                'command': 'thanks',
                'args': {'client_type': 'MCP'},
                'from': client_id,
                'timestamp':  datetime.now().isoformat()
            })
        else:
            logger.warning("クライアントIDが不明なため、感謝のメッセージを送信できません")

    async def _get_model_list(self) -> dict:
        """モデル一覧を取得"""
        response = await self._send_command({
            "type": "model",
            "command": "list",
            "args": ""
        })
        return response.get("data", {})

    async def _get_model_info(self, model_name: str) -> dict:
        """モデル情報を取得"""
        expressions = await self._send_command({
            "type": "model",
            "command": "get_expressions",
            "args": model_name
        })
        motions = await self._send_command({
            "type": "model",
            "command": "get_motions",
            "args": model_name
        })
        parameters = await self._send_command({
            "type": "model",
            "command": "get_parameters",
            "args": model_name
        })

        return {
            "model_name": model_name,
            "expressions": expressions.get("data", {}),
            "motions": motions.get("data", {}),
            "parameters": parameters.get("data", {}),
        }

    async def _set_expression(self, client_id: str, expression: str) -> dict:
        """表情を設定"""
        return await self._send_command({
            "type": "client",
            "command": "set_expression",
            "args": expression,
            "from": "mcp",
            "client_id": client_id
        })

    async def _set_motion(self, client_id: str, group: str, no: int, priority: int = 2) -> dict:
        """モーションを設定"""
        args = f"{group} {no} {priority}"
        return await self._send_command({
            "type": "client",
            "command": "set_motion",
            "args": args,
            "from": "mcp",
            "client_id": client_id
        })

    async def _set_parameter(self, client_id: str, parameters: dict) -> dict:
        """パラメータを設定"""
        return await self._send_command({
            "type": "client",
            "command": "set_parameter",
            "args": parameters,
            "from": "mcp",
            "client_id": client_id
        })

    async def _list_clients(self) -> dict:
        """クライアント一覧を取得"""
        response = await self._send_command({
            "type": "command",
            "command": "list"
        })
        return response.get("data", {})

    async def _get_client_state(self, client_id: str) -> dict:
        """クライアントの状態を取得"""
        # 各状態をWebSocketで取得
        model = await self._send_command({
            "type": "client",
            "command": "get_model_name",
            "from": "mcp",
            "client_id": client_id
        })
        expression = await self._send_command({
            "type": "client",
            "command": "get_expression",
            "from": "mcp",
            "client_id": client_id
        })
        motion = await self._send_command({
            "type": "client",
            "command": "get_motion",
            "from": "mcp",
            "client_id": client_id
        })
        eye_blink = await self._send_command({
            "type": "client",
            "command": "get_eye_blink",
            "from": "mcp",
            "client_id": client_id
        })
        breath = await self._send_command({
            "type": "client",
            "command": "get_breath",
            "from": "mcp",
            "client_id": client_id
        })
        idle_motion = await self._send_command({
            "type": "client",
            "command": "get_idle_motion",
            "from": "mcp",
            "client_id": client_id
        })
        drag_follow = await self._send_command({
            "type": "client",
            "command": "get_drag_follow",
            "from": "mcp",
            "client_id": client_id
        })
        physics = await self._send_command({
            "type": "client",
            "command": "get_physics",
            "from": "mcp",
            "client_id": client_id
        })
        position = await self._send_command({
            "type": "client",
            "command": "get_position",
            "from": "mcp",
            "client_id": client_id
        })
        scale = await self._send_command({
            "type": "client",
            "command": "get_scale",
            "from": "mcp",
            "client_id": client_id
        })

        return {
            "client_id": client_id,
            "model": model.get("data"),
            "expression": expression.get("data"),
            "motion": motion.get("data"),
            "eye_blink": eye_blink.get("data"),
            "breath": breath.get("data"),
            "idle_motion": idle_motion.get("data"),
            "drag_follow": drag_follow.get("data"),
            "physics": physics.get("data"),
            "position": position.get("data"),
            "scale": scale.get("data"),
        }

    async def _set_eye_blink(self, client_id: str, enabled: bool) -> dict:
        """まばたきを設定"""
        state = "enabled" if enabled else "disabled"
        return await self._send_command({
            "type": "client",
            "command": "set_eye_blink",
            "args": state,
            "from": "mcp",
            "client_id": client_id
        })

    async def _set_breath(self, client_id: str, enabled: bool) -> dict:
        """呼吸を設定"""
        state = "enabled" if enabled else "disabled"
        return await self._send_command({
            "type": "client",
            "command": "set_breath",
            "args": state,
            "from": "mcp",
            "client_id": client_id
        })

    async def _notify(self, message: str) -> dict:
        """状態を通知"""
        await self._send_notify({
            "type": "command",
            "command": f"notify {message}"
        })
        return {"status": "notified"}

    async def run_stdio(self):
        """MCPサーバーを起動"""
        logger.info("MCP Server starting...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )

    async def run_sse_v2(self, host: str, port: int):
        """MCPサーバーをSSE (HTTP) 経由で起動"""
        # SSEトランスポートを作成
        sse = SseServerTransport("/messages")

        async def handle_sse(scope, receive, send):
            """SSE接続エンドポイント (ASGI callable)"""
            async with sse.connect_sse(scope, receive, send) as streams:
                await self.server.run(
                    streams[0], streams[1],
                    self.server.create_initialization_options()
                )

        async def handle_messages(scope, receive, send):
            """メッセージ送信エンドポイント (ASGI callable)"""
            # Validate HTTP method
            if scope["type"] == "http" and scope["method"] != "POST":
                await send({
                    'type': 'http.response.start',
                    'status': 405,
                    'headers': [[b'allow', b'POST']],
                })
                await send({
                    'type': 'http.response.body',
                    'body': b'Method Not Allowed',
                })
                return
            await sse.handle_post_message(scope, receive, send)

        # Starlette アプリケーションを作成
        app = Starlette(
            routes=[
                Mount("/sse", app=handle_sse),
                Mount("/messages", app=handle_messages),
            ]
        )

        # ログフォーマットをカスタマイズ
        log_config = uvicorn.config.LOGGING_CONFIG
        log_config["formatters"]["default"]["fmt"] = \
            "%(levelname)s: %(asctime)s [MCP/Uvicorn]\t%(message)s"
        log_config["formatters"]["access"]["fmt"] =\
            '%(levelname)s: %(asctime)s [MCP/Access]\t%(client_addr)s - "%(request_line)s" %(status_code)s'

        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            log_config=log_config
        )
        # Uvicorn サーバーで起動
        self.uvicorn_server = uvicorn.Server(config)
        await self.uvicorn_server.serve()

    async def run_sse_v1(self, host: str, port: int):
        """MCPサーバーをSSE (HTTP) 経由で起動"""
        # SSEトランスポートを作成
        sse = SseServerTransport("/messages")

        async def handle_sse(request: Request):
            """SSE接続エンドポイント"""
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await self.server.run(
                    streams[0], streams[1],
                    self.server.create_initialization_options()
                )
            return None

        async def handle_messages(request: Request):
            """メッセージ送信エンドポイント"""
            await sse.handle_post_message(
                request.scope, request.receive, request._send
            )
            return None

        # Starlette アプリケーションを作成
        app = Starlette(
            routes=[
                Route("/sse", endpoint=handle_sse),
                Route("/messages", endpoint=handle_messages, methods=["POST"]),
            ]
        )

        # ログフォーマットをカスタマイズ
        log_config = uvicorn.config.LOGGING_CONFIG
        log_config["formatters"]["default"]["fmt"] = \
            "%(levelname)s: %(asctime)s [MCP/Uvicorn]\t%(message)s"
        log_config["formatters"]["access"]["fmt"] =\
            '%(levelname)s: %(asctime)s [MCP/Access]\t%(client_addr)s - "%(request_line)s" %(status_code)s'

        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            log_config=log_config
        )
        # Uvicorn サーバーで起動
        self.uvicorn_server = uvicorn.Server(config)
        await self.uvicorn_server.serve()

    async def run(self, host: str, port: int, websocket_url: str, is_sse: bool = True):
        """MCPサーバーを起動"""
        # Cubism Controllerに接続
        try:
            timeout_counter = 10
            while True:
                try:
                    self.websocket = await websockets.connect(websocket_url)
                    async for message in self.websocket:
                        try:
                            data = json.loads(message)
                            msg_type = data.get("type")
                            if msg_type == "welcome":
                                await self._send_thank_you_message(data.get("client_id", "unknown"))
                                logger.info(
                                    f"MCP <--> Cubism Controllerの接続しました")
                                break
                        except:
                            raise Exception("Invalid message format received")
                    break
                except Exception as e:
                    if timeout_counter <= 0:
                        raise RuntimeError(
                            f"Failed to connect to MCP <--> Cubism Controller at {websocket_url}") from e
                    logger.error(f"MCP <--> Cubism Controllerの接続できません: {e}")
                    logger.info("3秒後に再試行します...")
                    timeout_counter -= 1
                await asyncio.sleep(3)

            logger.info(f"MCP Server starting on http://{host}:{port}/sse")

            if is_sse:
                await self.run_sse_v1(host, port)
            else:
                await self.run_stdio()

        finally:
            # WebSocket接続を閉じる
            if self.websocket is not None:
                await self.websocket.close()

    async def stop(self):
        """MCPサーバーを停止"""
        if self.uvicorn_server:
            logger.info("MCPサーバーを停止しています...")
            self.uvicorn_server.should_exit = True
        else:
            logger.warning("MCPサーバーは起動していません")


async def stop_mcp_server():
    """グローバルなMCPサーバーインスタンスを停止"""
    global mcp_server
    if mcp_server is not None:
        await mcp_server.stop()


async def run_mcp(websocket_url: str = "ws://localhost:8765",
                  host: str = "0.0.0.0", port: int = 3001,
                  is_sse: bool = True, delay: float = 0.5):
    """
    MCPサーバーを起動

    Args:
        websocket_url: Cubism ControllerのURL（例: ws://localhost:8765）
        host: MCPサーバーのバインドホスト
        port: MCPサーバーのバインドポート
        is_sse: SSEモードを有効にするかどうか
        delay: サーバー起動前の待機時間（秒）
    """
    global mcp_server
    # MCPモードチェック
    if not MCP_AVAILABLE:
        logger.error("MCPモジュールがインストールされていません。"
                     "pip install mcp を実行してください")
        return

    mcp_server = MCPHandler()

    try:
        if delay > 0:
            await asyncio.sleep(delay)
        await mcp_server.run(host=host, port=port, websocket_url=websocket_url, is_sse=is_sse)
    except Exception as e:
        logger.error(f"MCPサーバーエラー: {e}")
    finally:
        await mcp_server.stop()
        logger.info("MCPサーバーは正常に停止しました")
