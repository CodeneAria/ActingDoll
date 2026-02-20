"""
MCP Server Handler for unified server
MCPサーバーハンドラー
"""
import asyncio
import logging
from fastmcp import FastMCP
from typing import Dict
import json
from datetime import datetime
import websockets
import uvicorn
from typing import Any


logger = logging.getLogger("MCPHandler")
logging.getLogger('docket.worker').setLevel(logging.WARNING)

mcp_server = None  # グローバルなMCPサーバーインスタンス


class MCPHandler:
    """MCP handler"""
    log_level = logging.getLevelName(logging.INFO)
    websocket = None
    is_running = False

    def __init__(self):
        """Initialize MCP server"""
        self.mcp = FastMCP(
            name="acting-doll",
            instructions="Live2Dモデル制御のためのMCPサーバー"
        )
        self._setup_tools()
        self._setup_resources()
        self._setup_prompts()

    ###########################################################
    # — Tool を追加 —
    ###########################################################
    def _setup_tools(self):
        """ツール定義をセットアップ"""
        @self.mcp.tool()
        async def list_clients() -> dict:
            """接続中のクライアント一覧を取得します"""
            # list
            return await self._list_clients()

        @self.mcp.tool()
        async def get_model_list() -> dict:
            """利用可能なLive2Dモデルの一覧を取得します"""
            # model list
            return await self._get_model_list()

        @self.mcp.tool()
        async def get_model_info(model_name: str) -> dict:
            """指定したモデルの詳細情報（expressions、motions、parameters）を取得します"""
            # model get_expressions <name>
            # model get_motions <name>
            # model get_parameters <name>
            return await self._get_model_info(model_name)

        @self.mcp.tool()
        async def set_expression(client_id: str, expression: str) -> dict:
            """クライアントのモデルの表情を設定します"""
            # client <client_id> set_expression [expression_name]
            return await self._set_expression(client_id, expression)

        @self.mcp.tool()
        async def set_motion(client_id: str, group: str, no: int, priority: int = 2) -> dict:
            """クライアントのモデルのモーションを再生します"""
            # client <client_id> set_motion [group_name] [no] [priority(0-3, default:2)]
            return await self._set_motion(client_id, group, no, priority)

        @self.mcp.tool()
        async def set_parameter(client_id: str, parameters: dict) -> dict:
            """クライアントのモデルのパラメータを設定します"""
            # client <client_id> set_parameter ID01=VALUE01 ID02=VALUE02 ...
            return await self._set_parameter(client_id, parameters)

        @self.mcp.tool()
        async def get_client_state(client_id: str) -> dict:
            """クライアントの現在の状態（モデル、表情、モーション等）を取得します"""
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
            return await self._get_client_state(client_id)

        @self.mcp.tool()
        async def set_eye_blink(client_id: str, enabled: bool) -> dict:
            """まばたき機能の有効/無効を設定します"""
            # client <client_id> set_eye_blink [enabled|disabled]
            return await self._set_eye_blink(client_id, enabled)

        @self.mcp.tool()
        async def set_breath(client_id: str, enabled: bool) -> dict:
            """呼吸エフェクトの有効/無効を設定します"""
            # client <client_id> set_breath [enabled|disabled]
            return await self._set_breath(client_id, enabled)

        @self.mcp.tool()
        async def notify(message: str) -> dict:
            """状態を通知します"""
            # notify <message>
            return await self._notify(message)

        # send <client_id> <message>
        #
        # client <client_id> set_idle_motion [enabled|disabled]
        # client <client_id> set_physics [enabled|disabled]
        # client <client_id> set_lipsync [base64_wav_data]
        # client <client_id> set_lipsync_from_file [filename]
        # client <client_id> set_position [x] [y] <relative>
        # client <client_id> set_scale [size]
        # client <client_id> set_drag_follow [enabled|disabled]

    ###########################################################
    # — Resource を追加 —
    ###########################################################

    def _setup_resources(self):
        @self.mcp.resource("app://config")
        def get_config() -> Dict[str, str]:
            """アプリケーションの設定情報を返すリソース"""
            return {
                "version": "1.0.0",
                "maintainer": "YourName",
                "features": "greet, sum, fetch"
            }
        # 動的テンプレート URI リソース（URI の中にパラメータ {name} を含む例）

        @self.mcp.resource("user://{name}")
        def get_user_profile(name: str) -> Dict[str, str]:
            """ユーザープロファイル情報を返すリソース"""
            # 実際には DB などから取る想定
            return {
                "name": name,
                "role": "user",
                "welcome_msg": f"Welcome, {name}!"
            }

    ###########################################################
    # — Prompt を追加 —
    ###########################################################
    def _setup_prompts(self):
        @self.mcp.prompt()
        def ask_for_sum(nums: list[int]) -> str:
            """合計を求めるプロンプトテンプレート"""
            return "次の数字の合計を求めてください：" + ", ".join(str(n) for n in nums)

        @self.mcp.prompt()
        def greet_user(name: str) -> str:
            """挨拶を促すプロンプトテンプレート"""
            return f"Hi, my name is {name}. Nice to meet you!"

    ###########################################################
    # Functions
    ###########################################################
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
        """クライアントに返信メッセージを送る"""
        if client_id != "unknown":
            await self._send_notify({
                'type': 'client',
                'command': 'thanks',
                'args': {'client_type': 'MCP'},
                'from': client_id,
                'timestamp': datetime.now().isoformat()
            })
        else:
            logger.warning("クライアントIDが不明なため、送信できません")

    ###########################################################
    # Control Functions
    ###########################################################
    def _greet(name: str) -> str:
        """指定された名前への挨拶を返す"""
        return f"Hello, {name}!"

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

    ###########################################################
    # Run Functions
    ###########################################################
    async def setup_websocket(self, websocket_url: str, delay_start: float):
        """WebSocketをセットアップ"""
        timeout_counter = 10
        if delay_start > 0:
            await asyncio.sleep(delay_start)
        while self.is_running:
            try:
                self.websocket = await websockets.connect(websocket_url)
                async for message in self.websocket:
                    data = json.loads(message)
                    msg_type = data.get("type")
                    if msg_type == "welcome":
                        await self._send_thank_you_message(data.get("client_id", "unknown"))
                        logger.info("MCP <--> Cubism Controllerの接続しました")
                        return
            except Exception as e:
                if timeout_counter <= 0:
                    raise RuntimeError(
                        f"Failed to connect to MCP <--> Cubism Controller at {websocket_url}") from e
                logger.error(f"MCP <--> Cubism Controllerの接続できません: {e}")
                logger.info("3秒後に再試行します...")
                timeout_counter -= 1
                await asyncio.sleep(3)

    async def run(self, websocket_url: str, host: str, port: int,
                  is_stdio: bool, delay_start: float):
        """MCPサーバーを実行"""
        self.is_running = True
        try:
            await self.setup_websocket(websocket_url, delay_start)

            if is_stdio:
                # 標準入出力で動かす場合
                await self.mcp.run_async(transport="stdio",
                                         log_level=self.log_level,
                                         show_banner=False)
            else:
                # Uvicornのログフォーマットをカスタマイズ
                log_config = uvicorn.config.LOGGING_CONFIG
                log_config["formatters"]["default"]["fmt"] = \
                    "%(levelname)s: %(asctime)s [MCP/Uvicorn]\t%(message)s"
                log_config["formatters"]["access"]["fmt"] = \
                    '%(levelname)s: %(asctime)s [MCP/Access]\t%(client_addr)s - "%(request_line)s" %(status_code)s'
                uvicorn_config: dict[str, Any] = {
                    "log_config": log_config,
                    "log_level": "info"
                }
                # SSE で動かす場合
                #   middleware: list[ASGIMiddleware] = None
                #   json_response: bool = False
                #   stateless_http: bool = False
                transport = "sse"  # or "streamable-http"
                await self.mcp.run_async(
                    transport=transport,
                    host=host,
                    port=port,
                    path="/sse",
                    log_level=self.log_level,
                    uvicorn_config=uvicorn_config,
                    show_banner=False
                )
        except KeyboardInterrupt:
            logger.info("MCPサーバーを停止しました")
        except Exception as e:
            raise RuntimeError(f"{e}")
        finally:
            await self.stop()

    async def stop(self):
        """MCPサーバーを停止"""
        self.is_running = False
        # WebSocket接続を閉じる
        if self.websocket is not None:
            await self.websocket.close()
        if self.mcp:
            logger.info("MCPサーバーを停止しています...")
            # 外部から止める方法はまだ FastMCP にないため、ここでは何もしない
            pass
        else:
            logger.warning("MCPサーバーは起動していません")


async def stop_mcp_server():
    """グローバルなMCPサーバーインスタンスを停止"""
    global mcp_server
    if mcp_server is not None:
        await mcp_server.stop()


async def run_mcp(websocket_url: str = "ws://localhost:8765",
                  host: str = "0.0.0.0", port: int = 3001,
                  is_stdio: bool = False,
                  delay_start: float = 0.5):
    """
    MCP サーバーのエントリーポイント

    Args:
        websocket_url: Cubism ControllerのURL（例: ws://localhost:8765）
        host: MCPサーバーのバインドホスト
        port: MCPサーバーのバインドポート
        is_stdio: STDIOモードを有効にするかどうか
        show_banner: バナーを表示するかどうか
        delay_start: サーバー起動前の待機時間（秒）
    """
    global mcp_server
    try:
        mcp_server = MCPHandler()
        await mcp_server.run(websocket_url=websocket_url,
                             host=host, port=port,
                             is_stdio=is_stdio,
                             delay_start=delay_start)
    except Exception as e:
        raise RuntimeError(f"<MCP>{e}")
