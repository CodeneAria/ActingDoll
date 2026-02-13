"""
MCP Server Handler for unified server
MCPサーバーハンドラー
"""

import json
import logging
from typing import Any

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.sse import SseServerTransport
    from mcp.types import TextContent, Tool
    from starlette.applications import Starlette
    from starlette.routing import Mount
    import uvicorn
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

logger = logging.getLogger("MCP")
logger.setLevel(logging.WARNING)


class MCPServerHandler:
    """MCP Server handler for unified server"""

    def __init__(self, model_command, client_command, process_command):
        """Initialize MCP server

        Args:
            model_command: Functions to handle model commands
            client_command: Function to handle client commands
            process_command: Function to process commands
        """
        if not MCP_AVAILABLE:
            raise RuntimeError("MCPモジュールがインストールされていません")

        self.server = Server("acting-doll")
        self.model_command = model_command
        self.client_command = client_command
        self.process_command = process_command
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
                ),
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

    async def _get_model_list(self) -> dict:
        """モデル一覧を取得"""
        result = await self.model_command("list", "", "mcp")
        return result.get("data", {})

    async def _get_model_info(self, model_name: str) -> dict:
        """モデル情報を取得"""
        expressions = await self.model_command("get_expressions", model_name, "mcp")
        motions = await self.model_command("get_motions", model_name, "mcp")
        parameters = await self.model_command("get_parameters", model_name, "mcp")

        return {
            "model_name": model_name,
            "expressions": expressions.get("data", {}),
            "motions": motions.get("data", {}),
            "parameters": parameters.get("data", {}),
        }

    async def _set_expression(self, client_id: str, expression: str) -> dict:
        """表情を設定"""
        return await self.client_command("set_expression", expression, client_id, "mcp")

    async def _set_motion(self, client_id: str, group: str, no: int, priority: int = 2) -> dict:
        """モーションを設定"""
        args = f"{group} {no} {priority}"
        return await self.client_command("set_motion", args, client_id, "mcp")

    async def _set_parameter(self, client_id: str, parameters: dict) -> dict:
        """パラメータを設定"""
        return await self.client_command("set_parameter", parameters, client_id, "mcp")

    async def _list_clients(self) -> dict:
        """クライアント一覧を取得"""
        result = await self.process_command("list", "mcp")
        return result.get("data", {})

    async def _get_client_state(self, client_id: str) -> dict:
        """クライアントの状態を取得"""
        model = await self.client_command("get_model", "", client_id, "mcp")
        expression = await self.client_command("get_expression", "", client_id, "mcp")
        motion = await self.client_command("get_motion", "", client_id, "mcp")
        eye_blink = await self.client_command("get_eye_blink", "", client_id, "mcp")
        breath = await self.client_command("get_breath", "", client_id, "mcp")
        idle_motion = await self.client_command("get_idle_motion", "", client_id, "mcp")
        drag_follow = await self.client_command("get_drag_follow", "", client_id, "mcp")
        physics = await self.client_command("get_physics", "", client_id, "mcp")
        position = await self.client_command("get_position", "", client_id, "mcp")
        scale = await self.client_command("get_scale", "", client_id, "mcp")

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
        return await self.client_command("set_eye_blink", state, client_id, "mcp")

    async def _set_breath(self, client_id: str, enabled: bool) -> dict:
        """呼吸を設定"""
        state = "enabled" if enabled else "disabled"
        return await self.client_command("set_breath", state, client_id, "mcp")

    async def _notify(self, message: str) -> dict:
        """状態を通知"""
        await self.process_command(f"notify {message}", "mcp")
        return {"status": "notified"}

    async def run(self, host: str = "0.0.0.0", port: int = 3001):
        """MCPサーバーをSSE (HTTP) 経由で起動"""
        logger.info(f"MCP Server starting on http://{host}:{port}/sse")

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
            await sse.handle_post_message(scope, receive, send)

        # Starlette アプリケーションを作成
        app = Starlette(
            routes=[
                Mount("/sse", app=handle_sse),
                Mount("/messages", app=handle_messages),
            ]
        )

        # Uvicorn サーバーで起動
        # ログフォーマットをカスタマイズ
        log_config = uvicorn.config.LOGGING_CONFIG
        log_config["formatters"]["default"]["fmt"] = \
            "%(levelname)s: [MCP/Uvicorn]\t%(asctime)s\t%(message)s"
        log_config["formatters"]["access"]["fmt"] =\
            '%(levelname)s: [MCP/Access]\t%(asctime)s\t%(client_addr)s - "%(request_line)s" %(status_code)s'

        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="warning",
            log_config=log_config
        )
        self.uvicorn_server = uvicorn.Server(config)
        await self.uvicorn_server.serve()

    async def stop(self):
        """MCPサーバーを停止"""
        if self.uvicorn_server:
            logger.info("MCPサーバーを停止しています...")
            self.uvicorn_server.should_exit = True
        else:
            logger.warning("MCPサーバーは起動していません")
