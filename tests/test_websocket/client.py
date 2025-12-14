"""
WebSocket Client for bidirectional communication
クライアント側のWebSocket通信アプリケーション
"""
import asyncio
import json
import logging
from datetime import datetime
import websockets

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
host = "localhost"
port = 8765


class WebSocketClient:
    """WebSocketクライアントクラス"""

    def __init__(self, uri: str = f"ws://{host}:{port}"):
        """
        初期化

        Args:
            uri: WebSocketサーバーのURI
        """
        self.uri = uri
        self.websocket = None
        self.running = False

    async def connect(self):
        """サーバーに接続"""
        logger.info(f"サーバーに接続中: {self.uri}")
        self.websocket = await websockets.connect(self.uri)
        logger.info("接続しました")
        self.running = True

    async def disconnect(self):
        """サーバーから切断"""
        if self.websocket:
            self.running = False
            await self.websocket.close()
            logger.info("切断しました")

    async def send_message(self, message: dict):
        """
        メッセージを送信

        Args:
            message: 送信するメッセージ（辞書形式）
        """
        if self.websocket:
            message_json = json.dumps(message, ensure_ascii=False)
            await self.websocket.send(message_json)
            logger.info(f"送信: {message}")

    async def send_echo(self, text: str):
        """エコーメッセージを送信"""
        await self.send_message({
            "type": "echo",
            "text": text,
            "timestamp": datetime.now().isoformat()
        })

    async def send_broadcast(self, content: str):
        """ブロードキャストメッセージを送信"""
        await self.send_message({
            "type": "broadcast",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    async def send_command(self, command: str):
        """コマンドを送信"""
        await self.send_message({
            "type": "command",
            "command": command,
            "timestamp": datetime.now().isoformat()
        })

    async def receive_messages(self):
        """メッセージ受信ループ"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"受信: {data}")
                    await self.handle_message(data)
                except json.JSONDecodeError:
                    logger.error(f"不正なJSON形式: {message}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("サーバーとの接続が切断されました")
            self.running = False

    async def handle_message(self, data: dict):
        """
        受信したメッセージを処理

        Args:
            data: 受信したメッセージ
        """
        msg_type = data.get("type", "unknown")

        if msg_type == "welcome":
            logger.info(f"ウェルカムメッセージ: {data.get('message')}")
        elif msg_type == "echo_response":
            logger.info(f"エコー応答: {data.get('original')}")
        elif msg_type == "broadcast_message":
            logger.info(f"ブロードキャスト from {data.get('from')}: {data.get('content')}")
        elif msg_type == "client_connected":
            logger.info(f"新しいクライアントが接続しました (合計: {data.get('total_clients')})")
        elif msg_type == "client_disconnected":
            logger.info(f"クライアントが切断しました (合計: {data.get('total_clients')})")
        elif msg_type == "command_response":
            logger.info(f"コマンド応答: {data}")
        elif msg_type == "error":
            logger.error(f"エラー: {data.get('message')}")

    async def interactive_mode(self):
        """対話モード"""
        logger.info("\n=== 対話モード ===")
        logger.info("コマンド:")
        logger.info("  echo <text>      - エコーメッセージを送信")
        logger.info("  broadcast <text> - ブロードキャストメッセージを送信")
        logger.info("  status           - サーバーステータスを取得")
        logger.info("  ping             - Pingを送信")
        logger.info("  quit             - 終了")
        logger.info("==================\n")

        while self.running:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, "> "
                )

                if not user_input.strip():
                    continue

                parts = user_input.strip().split(maxsplit=1)
                command = parts[0].lower()

                if command == "quit":
                    break
                elif command == "echo" and len(parts) > 1:
                    await self.send_echo(parts[1])
                elif command == "broadcast" and len(parts) > 1:
                    await self.send_broadcast(parts[1])
                elif command in ["status", "ping"]:
                    await self.send_command(command)
                else:
                    logger.warning(f"不明なコマンド: {command}")

            except EOFError:
                break
            except Exception as e:
                logger.error(f"エラー: {e}")


async def demo_automatic():
    """自動デモモード"""
    client = WebSocketClient()

    try:
        await client.connect()

        # 受信タスクを開始
        receive_task = asyncio.create_task(client.receive_messages())

        # デモメッセージを送信
        await asyncio.sleep(1)
        await client.send_echo("Hello from client!")

        await asyncio.sleep(2)
        await client.send_broadcast("こんにちは、みなさん！")

        await asyncio.sleep(2)
        await client.send_command("status")

        await asyncio.sleep(2)
        await client.send_command("ping")

        # 少し待機
        await asyncio.sleep(3)

        # 切断
        receive_task.cancel()
        await client.disconnect()

    except Exception as e:
        logger.error(f"エラー発生: {e}")


async def main_interactive():
    """対話モードでクライアントを起動"""
    client = WebSocketClient()

    try:
        await client.connect()

        # 受信タスクと対話タスクを並行実行
        receive_task = asyncio.create_task(client.receive_messages())
        interactive_task = asyncio.create_task(client.interactive_mode())

        # どちらかが終了するまで待機
        done, pending = await asyncio.wait(
            [receive_task, interactive_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # 残りのタスクをキャンセル
        for task in pending:
            task.cancel()

        await client.disconnect()

    except Exception as e:
        logger.error(f"エラー発生: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # デモモード
        logger.info("=== 自動デモモード ===")
        asyncio.run(demo_automatic())
    else:
        # 対話モード
        try:
            asyncio.run(main_interactive())
        except KeyboardInterrupt:
            logger.info("\nクライアントを終了しました")
