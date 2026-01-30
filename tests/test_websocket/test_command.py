"""
WebSocket Command Test Client
WebSocketサーバーのコマンドをテストするクライアント

1. **TestBasicCommands** - 基本コマンドのテスト
   - `test_list_command`: 接続クライアントリストの取得
   - `test_notify_command`: 全クライアントへの通知
   - `test_send_command`: 特定クライアントへのメッセージ送信

2. **TestModelCommands** - モデル情報コマンドのテスト
   - `test_model_list`: 利用可能なLive2Dモデルのリスト取得
   - `test_model_get_expressions`: モデルの表情リスト取得
   - `test_model_get_motions`: モデルのモーションリスト取得
   - `test_model_get_parameters`: モデルのパラメータリスト取得

3. **TestClientGetters** - クライアント状態取得のテスト
   - `test_get_eye_blink`: 瞬き機能の状態取得
   - `test_get_breath`: 呼吸機能の状態取得
   - `test_get_idle_motion`: アイドルモーションの状態取得
   - `test_get_drag_follow`: ドラッグ追従の状態取得
   - `test_get_physics`: 物理演算の状態取得
   - `test_get_expression`: 現在の表情取得
   - `test_get_motion`: 現在のモーション取得
   - `test_get_model`: 現在のモデル取得

4. **TestClientSetters** - クライアント設定変更のテスト
   - `test_set_eye_blink`: 瞬き機能の有効/無効化
   - `test_set_breath`: 呼吸機能の有効/無効化
   - `test_set_idle_motion`: アイドルモーションの有効/無効化
   - `test_set_drag_follow`: ドラッグ追従の有効/無効化
   - `test_set_physics`: 物理演算の有効/無効化
   - `test_set_expression`: 表情の設定
   - `test_set_motion`: モーションの再生
   - `test_set_parameter`: パラメータの直接設定
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List
import pytest
import pytest_asyncio
import websockets

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# WebSocket接続設定
HOST = "localhost"
PORT = 8765
WS_URI = f"ws://{HOST}:{PORT}"


class CommandTestClient:
    """WebSocketコマンドテストクライアント"""

    def __init__(self, uri: str = WS_URI):
        """
        初期化

        Args:
            uri: WebSocketサーバーのURI
        """
        self.uri = uri
        self.websocket = None
        self.running = False
        self.client_id = None

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


# pytest fixtures
@pytest_asyncio.fixture
async def ws_client():
    """WebSocketクライアントのfixture"""
    client = CommandTestClient()
    await client.connect()
    await asyncio.sleep(0.5)
    yield client
    await client.disconnect()


@pytest_asyncio.fixture
async def client_with_id(ws_client):
    """client_idを取得済みのクライアントfixture"""
    response = await ws_client.send_command("list")
    if response.get('data', {}).get('clients'):
        ws_client.client_id = response['data']['clients'][0]
    yield ws_client


@pytest_asyncio.fixture
async def model_info(ws_client):
    """モデル情報を取得するfixture"""
    response = await ws_client.send_command("model list")
    models = response.get('data', {}).get('models', [])
    model_name = models[0] if models else None

    if not model_name:
        pytest.skip("No models available")

    # 表情取得
    exp_response = await ws_client.send_command(f"model get_expressions {model_name}")
    expressions = exp_response.get('data', {}).get('expressions', [])

    # モーション取得
    motion_response = await ws_client.send_command(f"model get_motions {model_name}")
    motions = motion_response.get('data', {}).get('motions', {})

    return {
        'model_name': model_name,
        'expressions': expressions,
        'motions': motions
    }


# テストクラス: 基本コマンド
class TestBasicCommands:
    """基本コマンドのテスト"""

    @pytest.mark.asyncio
    async def test_list_command(self, ws_client):
        """listコマンドのテスト"""
        await ws_client.send_command("list")
        response = await ws_client.send_command("list")

        assert response.get("type") == "command_response"
        assert "data" in response
        assert "clients" in response["data"]
        logger.info(f"✅ Clients: {response['data']['clients']}")

    @pytest.mark.asyncio
    async def test_notify_command(self, ws_client):
        """notifyコマンドのテスト"""
        await ws_client.send_command("notify テストメッセージ")
        response = await ws_client.send_command("notify テストメッセージ")

        assert response.get("type") == "notify"
        assert "message" in response
        logger.info(f"✅ Notify result: {response.get('message')}")

    @pytest.mark.asyncio
    async def test_send_command(self, client_with_id):
        """sendコマンドのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        await ws_client.send_command("list")
        response = await client_with_id.send_command(
            f"send {client_with_id.client_id} テストメッセージ"
        )

        assert response.get("type") == "command_response"
        logger.info(f"✅ Send to {client_with_id.client_id}: {response.get('result')}")


# テストクラス: モデル情報
class TestModelCommands:
    """モデル情報コマンドのテスト"""

    @pytest.mark.asyncio
    async def test_model_list(self, ws_client):
        """model listコマンドのテスト"""
        await ws_client.send_command("model list")
        response = await ws_client.send_command("model list")

        assert response.get("type") == "command_response"
        assert "data" in response
        models = response["data"]
        assert len(models) > 0
        logger.info(f"✅ Models: {models}")

    @pytest.mark.asyncio
    async def test_model_get_expressions(self, ws_client, model_info):
        """model get_expressionsコマンドのテスト"""
        model_name = model_info['model_name']
        response = await ws_client.send_command(f"model get_expressions {model_name}")

        assert response.get("type") == "command_response"
        assert "data" in response
        assert "expressions" in response["data"]
        logger.info(f"✅ Expressions: {response['data']['expressions']}")

    @pytest.mark.asyncio
    async def test_model_get_motions(self, ws_client, model_info):
        """model get_motionsコマンドのテスト"""
        model_name = model_info['model_name']
        response = await ws_client.send_command(f"model get_motions {model_name}")

        assert response.get("type") == "command_response"
        assert "data" in response
        assert "motions" in response["data"]
        motions = response["data"]["motions"]
        assert isinstance(motions, dict)
        logger.info(f"✅ Motion groups: {list(motions.keys())}")

    @pytest.mark.asyncio
    async def test_model_get_parameters(self, ws_client, model_info):
        """model get_parametersコマンドのテスト"""
        model_name = model_info['model_name']
        response = await ws_client.send_command(f"model get_parameters {model_name}")

        assert response.get("type") == "command_response"
        assert "data" in response
        assert "parameters" in response["data"]
        params = response["data"]["parameters"]
        assert len(params) > 0
        logger.info(f"✅ Parameters count: {len(params)}")


# テストクラス: クライアント状態取得
class TestClientGetters:
    """クライアント状態取得コマンドのテスト"""

    @pytest.mark.asyncio
    async def test_get_eye_blink(self, client_with_id):
        """client get_eye_blinkのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} get_eye_blink"
        )

        assert response.get("type") == "command_response"
        assert "data" in response
        assert "enabled" in response["data"]
        logger.info(f"✅ Eye blink enabled: {response['data']['enabled']}")

    @pytest.mark.asyncio
    async def test_get_breath(self, client_with_id):
        """client get_breathのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} get_breath"
        )

        assert response.get("type") == "command_response"
        assert "data" in response
        assert "enabled" in response["data"]
        logger.info(f"✅ Breath enabled: {response['data']['enabled']}")

    @pytest.mark.asyncio
    async def test_get_idle_motion(self, client_with_id):
        """client get_idle_motionのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} get_idle_motion"
        )

        assert response.get("type") == "command_response"
        assert "data" in response
        assert "enabled" in response["data"]
        logger.info(f"✅ Idle motion enabled: {response['data']['enabled']}")

    @pytest.mark.asyncio
    async def test_get_drag_follow(self, client_with_id):
        """client get_drag_followのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} get_drag_follow"
        )

        assert response.get("type") == "command_response"
        assert "data" in response
        assert "enabled" in response["data"]
        logger.info(f"✅ Drag follow enabled: {response['data']['enabled']}")

    @pytest.mark.asyncio
    async def test_get_physics(self, client_with_id):
        """client get_physicsのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} get_physics"
        )

        assert response.get("type") == "command_response"
        assert "data" in response
        assert "enabled" in response["data"]
        logger.info(f"✅ Physics enabled: {response['data']['enabled']}")

    @pytest.mark.asyncio
    async def test_get_expression(self, client_with_id):
        """client get_expressionのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} get_expression"
        )

        assert response.get("type") == "command_response"
        assert "data" in response
        logger.info(f"✅ Expression: {response['data'].get('expression')}")

    @pytest.mark.asyncio
    async def test_get_motion(self, client_with_id):
        """client get_motionのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} get_motion"
        )

        assert response.get("type") == "command_response"
        assert "data" in response
        logger.info(f"✅ Motion: {response['data'].get('motion')}")

    @pytest.mark.asyncio
    async def test_get_model(self, client_with_id):
        """client get_modelのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} get_model"
        )

        assert response.get("type") == "command_response"
        assert "data" in response
        assert "model" in response["data"]
        logger.info(f"✅ Model: {response['data']['model']}")


# テストクラス: クライアント設定変更
class TestClientSetters:
    """クライアント設定変更コマンドのテスト"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("enabled", ["enabled", "disabled"])
    async def test_set_eye_blink(self, client_with_id, enabled):
        """client set_eye_blinkのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} set_eye_blink {enabled}"
        )

        assert response.get("type") == "command_response"
        assert response.get("result") in ["success", "ok"]
        logger.info(f"✅ Set eye_blink to {enabled}")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("enabled", ["enabled", "disabled"])
    async def test_set_breath(self, client_with_id, enabled):
        """client set_breathのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} set_breath {enabled}"
        )

        assert response.get("type") == "command_response"
        assert response.get("result") in ["success", "ok"]
        logger.info(f"✅ Set breath to {enabled}")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("enabled", ["enabled", "disabled"])
    async def test_set_idle_motion(self, client_with_id, enabled):
        """client set_idle_motionのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} set_idle_motion {enabled}"
        )

        assert response.get("type") == "command_response"
        assert response.get("result") in ["success", "ok"]
        logger.info(f"✅ Set idle_motion to {enabled}")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("enabled", ["enabled", "disabled"])
    async def test_set_drag_follow(self, client_with_id, enabled):
        """client set_drag_followのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} set_drag_follow {enabled}"
        )

        assert response.get("type") == "command_response"
        assert response.get("result") in ["success", "ok"]
        logger.info(f"✅ Set drag_follow to {enabled}")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("enabled", ["enabled", "disabled"])
    async def test_set_physics(self, client_with_id, enabled):
        """client set_physicsのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} set_physics {enabled}"
        )

        assert response.get("type") == "command_response"
        assert response.get("result") in ["success", "ok"]
        logger.info(f"✅ Set physics to {enabled}")

    @pytest.mark.asyncio
    async def test_set_expression(self, client_with_id, model_info):
        """client set_expressionのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        expressions = model_info['expressions']
        if not expressions:
            pytest.skip("No expressions available")

        expression_name = expressions[0]
        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} set_expression {expression_name}"
        )

        assert response.get("type") == "command_response"
        assert response.get("result") in ["success", "ok"]
        logger.info(f"✅ Set expression to {expression_name}")

    @pytest.mark.asyncio
    async def test_set_motion(self, client_with_id, model_info):
        """client set_motionのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        motions = model_info['motions']
        if not motions:
            pytest.skip("No motions available")

        group_name = list(motions.keys())[0]
        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} set_motion {group_name} 0"
        )

        assert response.get("type") == "command_response"
        assert response.get("result") in ["success", "ok"]
        logger.info(f"✅ Set motion to {group_name} 0")

    @pytest.mark.asyncio
    async def test_set_parameter(self, client_with_id):
        """client set_parameterのテスト"""
        if not client_with_id.client_id:
            pytest.skip("No client_id available")

        response = await client_with_id.send_command(
            f"client {client_with_id.client_id} set_parameter ParamAngleX=15.0 ParamAngleY=-10.0"
        )

        assert response.get("type") == "command_response"
        assert response.get("result") in ["success", "ok"]
        logger.info(f"✅ Set parameters")


if __name__ == "__main__":
    # pytestを実行
    pytest.main([__file__, "-v", "-s"])
