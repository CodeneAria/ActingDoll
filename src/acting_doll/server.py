"""MCP server for Live2D control."""

import os

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from acting_doll.client import Live2DClient

# Initialize MCP server
server = Server("acting-doll")

# Get Live2D server URL from environment variable
LIVE2D_SERVER_URL = os.environ.get("LIVE2D_SERVER_URL", "http://localhost:8080")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for Live2D control."""
    return [
        Tool(
            name="set_parameter",
            description=(
                "Live2Dモデルのパラメータを設定します。"
                "例: ParamAngleX（顔の角度X）、ParamAngleY（顔の角度Y）、ParamAngleZ（顔の傾き）、"
                "ParamEyeLOpen（左目の開き具合）、ParamEyeROpen（右目の開き具合）、"
                "ParamMouthOpenY（口の開き具合）など。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "parameter_id": {
                        "type": "string",
                        "description": "パラメータID（例: ParamAngleX, ParamEyeLOpen）",
                    },
                    "value": {
                        "type": "number",
                        "description": "設定する値（角度は-30〜30、開閉は0〜1が一般的）",
                    },
                },
                "required": ["parameter_id", "value"],
            },
        ),
        Tool(
            name="set_expression",
            description=(
                "Live2Dモデルの表情を設定します。表情IDはモデルによって異なります。"
                "一般的な例: 'happy', 'sad', 'angry', 'surprised'など。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "expression_id": {
                        "type": "string",
                        "description": "表情ID（例: happy, sad, angry）",
                    },
                },
                "required": ["expression_id"],
            },
        ),
        Tool(
            name="start_motion",
            description=(
                "Live2Dモデルのモーションを開始します。"
                "モーショングループとインデックスを指定します。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "group": {
                        "type": "string",
                        "description": "モーショングループ名（例: Idle, TapBody）",
                    },
                    "index": {
                        "type": "integer",
                        "description": "モーションのインデックス（0から開始）",
                    },
                    "priority": {
                        "type": "integer",
                        "description": "モーション優先度（1=アイドル, 2=通常, 3=強制）",
                        "default": 2,
                    },
                },
                "required": ["group", "index"],
            },
        ),
        Tool(
            name="get_model_info",
            description=(
                "現在のLive2Dモデルの情報を取得します。"
                "利用可能なパラメータ、表情、モーションの一覧が含まれます。"
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="reset_pose",
            description="Live2Dモデルをデフォルトのポーズにリセットします。",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="set_look_at",
            description=(
                "Live2Dモデルの視線を設定します。X座標（左右）とY座標（上下）を指定します。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {
                        "type": "number",
                        "description": "X座標（-1.0〜1.0、左から右）",
                    },
                    "y": {
                        "type": "number",
                        "description": "Y座標（-1.0〜1.0、下から上）",
                    },
                },
                "required": ["x", "y"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls for Live2D control."""
    client = Live2DClient(base_url=LIVE2D_SERVER_URL)

    try:
        if name == "set_parameter":
            parameter_id = arguments["parameter_id"]
            value = float(arguments["value"])
            result = await client.set_parameter(parameter_id, value)
            return [
                TextContent(
                    type="text",
                    text=f"パラメータ '{parameter_id}' を {value} に設定しました。\n{result}",
                )
            ]

        elif name == "set_expression":
            expression_id = arguments["expression_id"]
            result = await client.set_expression(expression_id)
            return [
                TextContent(
                    type="text",
                    text=f"表情 '{expression_id}' を設定しました。\n{result}",
                )
            ]

        elif name == "start_motion":
            group = arguments["group"]
            index = int(arguments["index"])
            priority = int(arguments.get("priority", 2))
            result = await client.start_motion(group, index, priority)
            return [
                TextContent(
                    type="text",
                    text=f"モーション '{group}[{index}]' を開始しました。\n{result}",
                )
            ]

        elif name == "get_model_info":
            result = await client.get_model_info()
            return [
                TextContent(
                    type="text",
                    text=f"モデル情報:\n{result}",
                )
            ]

        elif name == "reset_pose":
            result = await client.reset_pose()
            return [
                TextContent(
                    type="text",
                    text=f"ポーズをリセットしました。\n{result}",
                )
            ]

        elif name == "set_look_at":
            x = float(arguments["x"])
            y = float(arguments["y"])
            result = await client.set_look_at(x, y)
            return [
                TextContent(
                    type="text",
                    text=f"視線を ({x}, {y}) に設定しました。\n{result}",
                )
            ]

        else:
            return [
                TextContent(
                    type="text",
                    text=f"エラー: 不明なツール '{name}'",
                )
            ]

    except Exception as e:
        return [
            TextContent(
                type="text",
                text=f"エラー: {e!s}",
            )
        ]

    finally:
        await client.close()


async def run_server() -> None:
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    """Entry point for the MCP server."""
    import asyncio

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
