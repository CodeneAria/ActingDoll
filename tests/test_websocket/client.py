"""
WebSocket Command Test Client
WebSocketサーバーのコマンドをテストするクライアント
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


class CommandTestClient:
    """WebSocketコマンドテストクライアント"""

    def __init__(self, uri: str = f"ws://{host}:{port}"):
        """
        初期化

        Args:
            uri: WebSocketサーバーのURI
        """
        self.uri = uri
        self.websocket = None
        self.running = False
        self.responses = []
        self.client_id = None
        self.test_results = []

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

    async def send_command(self, command: str) -> dict:
        """
        コマンドを送信して応答を待つ

        Args:
            command: 送信するコマンド

        Returns:
            サーバーからの応答
        """
        if not self.websocket:
            return {"error": "Not connected"}

        message = {
            "type": "command",
            "command": command,
            "timestamp": datetime.now().isoformat()
        }

        message_json = json.dumps(message, ensure_ascii=False)
        await self.websocket.send(message_json)
        logger.info(f"📤 送信: {command}")

        # 応答を待つ
        try:
            response_text = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            response = json.loads(response_text)
            logger.info(f"📥 受信: {response.get('type', 'unknown')}")
            return response
        except asyncio.TimeoutError:
            logger.error("⏱️  タイムアウト: 応答がありません")
            return {"error": "Timeout"}
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON解析エラー: {e}")
            return {"error": f"JSON decode error: {e}"}

    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """テスト結果をログに記録"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        logger.info(f"{status} | {test_name} | {details}")

    async def test_list_command(self):
        """list コマンドをテスト"""
        logger.info("\n=== Test: list ===")
        response = await self.send_command("list")

        success = response.get("type") == "command_response"
        self.log_test_result("list", success, f"Clients: {response.get('data', {}).get('clients', [])}")

        # client_idを保存
        if success and response.get('data', {}).get('clients'):
            self.client_id = response['data']['clients'][0] if response['data']['clients'] else None

        await asyncio.sleep(1)

    async def test_notify_command(self):
        """notify コマンドをテスト"""
        logger.info("\n=== Test: notify ===")
        response = await self.send_command("notify テストメッセージ")

        success = response.get("type") == "command_response"
        self.log_test_result("notify", success, f"Result: {response.get('result')}")
        await asyncio.sleep(1)

    async def test_send_command(self):
        """send コマンドをテスト"""
        logger.info("\n=== Test: send ===")
        if not self.client_id:
            self.log_test_result("send", False, "No client_id available")
            return

        response = await self.send_command(f"send {self.client_id} テストメッセージ")

        success = response.get("type") == "command_response"
        self.log_test_result("send", success, f"Client: {self.client_id}")
        await asyncio.sleep(1)

    async def test_model_list_command(self):
        """model list コマンドをテスト"""
        logger.info("\n=== Test: model list ===")
        response = await self.send_command("model list")

        success = response.get("type") == "command_response"
        models = response.get('data', {}).get('models', [])
        self.log_test_result("model list", success, f"Models: {models}")
        return models[0] if models else None

    async def test_model_get_expressions(self, model_name: str):
        """model get_expressions コマンドをテスト"""
        logger.info(f"=== Test: model get_expressions {model_name} ===")
        response = await self.send_command(f"model get_expressions {model_name}")

        success = response.get("type") == "command_response"
        expressions = response.get('data', {}).get('expressions', [])
        self.log_test_result("model get_expressions", success, f"Expressions: {expressions}")
        await asyncio.sleep(1)
        return expressions[0] if expressions else None

    async def test_model_get_motions(self, model_name: str):
        """model get_motions コマンドをテスト"""
        logger.info(f"=== Test: model get_motions {model_name} ===")
        response = await self.send_command(f"model get_motions {model_name}")

        success = response.get("type") == "command_response"
        motions = response.get('data', {}).get('motions', {})
        self.log_test_result("model get_motions", success, f"Motion groups: {list(motions.keys())}")
        await asyncio.sleep(1)
        return motions

    async def test_model_get_parameters(self, model_name: str):
        """model get_parameters コマンドをテスト"""
        logger.info(f"=== Test: model get_parameters {model_name} ===")
        response = await self.send_command(f"model get_parameters {model_name}")

        success = response.get("type") == "command_response"
        params = response.get('data', {}).get('parameters', [])
        self.log_test_result("model get_parameters", success, f"Parameters count: {len(params)}")
        await asyncio.sleep(1)

    async def test_client_get_eye_blink(self):
        """client get_eye_blink コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} get_eye_blink ===")
        if not self.client_id:
            self.log_test_result("client get_eye_blink", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} get_eye_blink")
        success = response.get("type") == "command_response"
        enabled = response.get('data', {}).get('enabled')
        self.log_test_result("client get_eye_blink", success, f"Enabled: {enabled}")
        await asyncio.sleep(1)

    async def test_client_set_eye_blink(self, enabled: str):
        """client set_eye_blink コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} set_eye_blink {enabled} ===")
        if not self.client_id:
            self.log_test_result("client set_eye_blink", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} set_eye_blink {enabled}")
        success = response.get("type") == "command_response"
        self.log_test_result(f"client set_eye_blink {enabled}", success, f"Result: {response.get('result')}")
        await asyncio.sleep(1)

    async def test_client_get_breath(self):
        """client get_breath コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} get_breath ===")
        if not self.client_id:
            self.log_test_result("client get_breath", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} get_breath")
        success = response.get("type") == "command_response"
        enabled = response.get('data', {}).get('enabled')
        self.log_test_result("client get_breath", success, f"Enabled: {enabled}")
        await asyncio.sleep(1)

    async def test_client_set_breath(self, enabled: str):
        """client set_breath コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} set_breath {enabled} ===")
        if not self.client_id:
            self.log_test_result("client set_breath", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} set_breath {enabled}")
        success = response.get("type") == "command_response"
        self.log_test_result(f"client set_breath {enabled}", success, f"Result: {response.get('result')}")
        await asyncio.sleep(1)

    async def test_client_get_idle_motion(self):
        """client get_idle_motion コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} get_idle_motion ===")
        if not self.client_id:
            self.log_test_result("client get_idle_motion", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} get_idle_motion")
        success = response.get("type") == "command_response"
        enabled = response.get('data', {}).get('enabled')
        self.log_test_result("client get_idle_motion", success, f"Enabled: {enabled}")
        await asyncio.sleep(1)

    async def test_client_set_idle_motion(self, enabled: str):
        """client set_idle_motion コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} set_idle_motion {enabled} ===")
        if not self.client_id:
            self.log_test_result("client set_idle_motion", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} set_idle_motion {enabled}")
        success = response.get("type") == "command_response"
        self.log_test_result(f"client set_idle_motion {enabled}", success, f"Result: {response.get('result')}")
        await asyncio.sleep(1)

    async def test_client_get_drag_follow(self):
        """client get_drag_follow コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} get_drag_follow ===")
        if not self.client_id:
            self.log_test_result("client get_drag_follow", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} get_drag_follow")
        success = response.get("type") == "command_response"
        enabled = response.get('data', {}).get('enabled')
        self.log_test_result("client get_drag_follow", success, f"Enabled: {enabled}")
        await asyncio.sleep(1)

    async def test_client_set_drag_follow(self, enabled: str):
        """client set_drag_follow コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} set_drag_follow {enabled} ===")
        if not self.client_id:
            self.log_test_result("client set_drag_follow", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} set_drag_follow {enabled}")
        success = response.get("type") == "command_response"
        self.log_test_result(f"client set_drag_follow {enabled}", success, f"Result: {response.get('result')}")
        await asyncio.sleep(1)

    async def test_client_get_physics(self):
        """client get_physics コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} get_physics ===")
        if not self.client_id:
            self.log_test_result("client get_physics", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} get_physics")
        success = response.get("type") == "command_response"
        enabled = response.get('data', {}).get('enabled')
        self.log_test_result("client get_physics", success, f"Enabled: {enabled}")
        await asyncio.sleep(1)

    async def test_client_set_physics(self, enabled: str):
        """client set_physics コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} set_physics {enabled} ===")
        if not self.client_id:
            self.log_test_result("client set_physics", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} set_physics {enabled}")
        success = response.get("type") == "command_response"
        self.log_test_result(f"client set_physics {enabled}", success, f"Result: {response.get('result')}")
        await asyncio.sleep(1)

    async def test_client_get_expression(self):
        """client get_expression コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} get_expression ===")
        if not self.client_id:
            self.log_test_result("client get_expression", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} get_expression")
        success = response.get("type") == "command_response"
        expression = response.get('data', {}).get('expression')
        self.log_test_result("client get_expression", success, f"Expression: {expression}")
        await asyncio.sleep(1)

    async def test_client_set_expression(self, expression_name: str):
        """client set_expression コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} set_expression {expression_name} ===")
        if not self.client_id:
            self.log_test_result("client set_expression", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} set_expression {expression_name}")
        success = response.get("type") == "command_response"
        self.log_test_result(f"client set_expression {expression_name}", success, f"Result: {response.get('result')}")
        await asyncio.sleep(1)

    async def test_client_get_motion(self):
        """client get_motion コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} get_motion ===")
        if not self.client_id:
            self.log_test_result("client get_motion", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} get_motion")
        success = response.get("type") == "command_response"
        motion = response.get('data', {}).get('motion')
        self.log_test_result("client get_motion", success, f"Motion: {motion}")
        await asyncio.sleep(1)

    async def test_client_set_motion(self, group_name: str, no: int):
        """client set_motion コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} set_motion {group_name} {no} ===")
        if not self.client_id:
            self.log_test_result("client set_motion", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} set_motion {group_name} {no}")
        success = response.get("type") == "command_response"
        self.log_test_result(f"client set_motion {group_name} {no}", success, f"Result: {response.get('result')}")
        await asyncio.sleep(1)

    async def test_client_get_model(self):
        """client get_model コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} get_model ===")
        if not self.client_id:
            self.log_test_result("client get_model", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} get_model")
        success = response.get("type") == "command_response"
        model = response.get('data', {}).get('model')
        self.log_test_result("client get_model", success, f"Model: {model}")
        await asyncio.sleep(1)

    async def test_client_set_parameter(self):
        """client set_parameter コマンドをテスト"""
        logger.info(f"=== Test: client {self.client_id} set_parameter ===")
        if not self.client_id:
            self.log_test_result("client set_parameter", False, "No client_id")
            return

        response = await self.send_command(f"client {self.client_id} set_parameter ParamAngleX=15.0 ParamAngleY=-10.0")
        success = response.get("type") == "command_response"
        self.log_test_result("client set_parameter", success, f"Result: {response.get('result')}")
        await asyncio.sleep(1)

    async def run_all_tests(self):
        """すべてのテストを実行"""
        logger.info("="*60)
        logger.info("WebSocket Command Test Suite")
        logger.info("="*60)

        try:
            await self.connect()
            await asyncio.sleep(1)

            # 基本コマンドのテスト
            await self.test_list_command()
            await self.test_notify_command()
            await self.test_send_command()

            # モデル情報のテスト
            model_name = await self.test_model_list_command()

            if model_name:
                expression_name = await self.test_model_get_expressions(model_name)
                motions = await self.test_model_get_motions(model_name)
                await self.test_model_get_parameters(model_name)

                # クライアント制御のテスト (get系)
                await self.test_client_get_eye_blink()
                await self.test_client_get_breath()
                await self.test_client_get_idle_motion()
                await self.test_client_get_drag_follow()
                await self.test_client_get_physics()
                await self.test_client_get_expression()
                await self.test_client_get_motion()
                await self.test_client_get_model()

                # クライアント制御のテスト (set系)
                await self.test_client_set_eye_blink("disabled")
                await self.test_client_set_eye_blink("enabled")

                await self.test_client_set_breath("disabled")
                await self.test_client_set_breath("enabled")

                await self.test_client_set_idle_motion("disabled")
                await self.test_client_set_idle_motion("enabled")

                await self.test_client_set_drag_follow("disabled")
                await self.test_client_set_drag_follow("enabled")

                await self.test_client_set_physics("disabled")
                await self.test_client_set_physics("enabled")

                # 表情とモーションの設定
                if expression_name:
                    await self.test_client_set_expression(expression_name)

                if motions:
                    group_name = list(motions.keys())[0]
                    await self.test_client_set_motion(group_name, 0)

                # パラメータの設定
                await self.test_client_set_parameter()

            # テスト結果のサマリー
            self.print_summary()

            await self.disconnect()

        except Exception as e:
            logger.error(f"テスト実行中にエラー: {e}")
            import traceback
            traceback.print_exc()

    def print_summary(self):
        """テスト結果のサマリーを表示"""
        logger.info("="*60)
        logger.info("Test Summary")
        logger.info("="*60)

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['success'])
        failed = total - passed

        logger.info(f"Total Tests: {total}")
        logger.info(f"✅ Passed: {passed}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "N/A")
        logger.info("="*60)


async def main():
    """メイン関数"""
    client = CommandTestClient()
    await client.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nテストを中断しました")
