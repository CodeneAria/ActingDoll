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
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

logger = logging.getLogger(__name__)


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
        self._setup_handlers()

    def _setup_handlers(self):
        """MCPサーバーのハンドラーを設定"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """利用可能なツール一覧を返す"""
            return [
                Tool(
                    name="get_model_list",
                    description="利用可能なLive2Dモデルの一覧を取得します",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
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
                    name="list_clients",
                    description="接続中のクライアント一覧を取得します",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
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

        return {
            "client_id": client_id,
            "model": model.get("data"),
            "expression": expression.get("data"),
            "motion": motion.get("data"),
            "eye_blink": eye_blink.get("data"),
            "breath": breath.get("data"),
        }

    async def _set_eye_blink(self, client_id: str, enabled: bool) -> dict:
        """まばたきを設定"""
        state = "enabled" if enabled else "disabled"
        return await self.client_command("set_eye_blink", state, client_id, "mcp")

    async def _set_breath(self, client_id: str, enabled: bool) -> dict:
        """呼吸を設定"""
        state = "enabled" if enabled else "disabled"
        return await self.client_command("set_breath", state, client_id, "mcp")

    async def run(self):
        """MCPサーバーを起動"""
        logger.info("MCP Server starting...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options(),
            )
