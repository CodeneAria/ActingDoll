"""
Tests for Acting Doll MCP Server
"""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from adapter.server.server import ActingDollMCPServer


class TestActingDollMCPServer:
    """MCPサーバーのテストクラス"""

    @pytest.fixture
    def server(self):
        """テスト用のサーバーインスタンスを作成"""
        return ActingDollMCPServer(ws_host="localhost", ws_port=8766)

    @pytest.mark.asyncio
    async def test_initialization(self, server):
        """初期化のテスト"""
        assert server.ws_host == "localhost"
        assert server.ws_port == 8766
        assert server.ws_url == "ws://localhost:8766"
        assert server.ws_connection is None

    @pytest.mark.asyncio
    async def test_ensure_ws_connection_success(self, server):
        """WebSocket接続が成功する場合のテスト"""
        mock_ws = AsyncMock()
        mock_ws.closed = False

        with patch("websockets.connect", return_value=mock_ws):
            await server._ensure_ws_connection()
            assert server.ws_connection == mock_ws

    @pytest.mark.asyncio
    async def test_ensure_ws_connection_failure(self, server):
        """WebSocket接続が失敗する場合のテスト"""
        with patch(
            "websockets.connect", side_effect=ConnectionError("Connection failed")
        ):
            with pytest.raises(ConnectionError) as exc_info:
                await server._ensure_ws_connection()
            assert "接続できませんでした" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_ws_command_success(self, server):
        """コマンド送信が成功する場合のテスト"""
        mock_ws = AsyncMock()
        mock_ws.closed = False
        response_data = {"status": "ok", "result": "success"}
        mock_ws.recv.return_value = json.dumps(response_data)

        with patch("websockets.connect", return_value=mock_ws):
            result = await server._send_ws_command("command", "test")
            assert result == response_data
            mock_ws.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_ws_command_timeout(self, server):
        """コマンド送信がタイムアウトする場合のテスト"""
        mock_ws = AsyncMock()
        mock_ws.closed = False
        mock_ws.recv.side_effect = asyncio.TimeoutError()

        with patch("websockets.connect", return_value=mock_ws):
            result = await server._send_ws_command("command", "test")
            assert "error" in result
            assert "タイムアウト" in result["error"]

    @pytest.mark.asyncio
    async def test_get_model_list(self, server):
        """モデル一覧取得のテスト"""
        expected_response = {
            "status": "ok",
            "models": ["Haru", "Hiyori", "Mark"],
        }

        with patch.object(
            server, "_send_ws_command", return_value=expected_response
        ) as mock_send:
            result = await server._get_model_list()
            assert result == expected_response
            mock_send.assert_called_once_with("model", "list")

    @pytest.mark.asyncio
    async def test_get_model_info(self, server):
        """モデル情報取得のテスト"""
        expressions_response = {"status": "ok",
                                "expressions": ["smile", "angry"]}
        motions_response = {"status": "ok", "motions": {"TapBody": [0, 1, 2]}}
        parameters_response = {
            "status": "ok",
            "parameters": ["ParamAngleX", "ParamAngleY"],
        }

        with patch.object(
            server,
            "_send_ws_command",
            side_effect=[
                expressions_response,
                motions_response,
                parameters_response,
            ],
        ):
            result = await server._get_model_info("Haru")
            assert result["model_name"] == "Haru"
            assert result["expressions"] == expressions_response
            assert result["motions"] == motions_response
            assert result["parameters"] == parameters_response

    @pytest.mark.asyncio
    async def test_set_expression(self, server):
        """表情設定のテスト"""
        expected_response = {"status": "ok", "message": "Expression set"}

        with patch.object(
            server, "_send_ws_command", return_value=expected_response
        ) as mock_send:
            result = await server._set_expression("127.0.0.1:12345", "smile")
            assert result == expected_response
            mock_send.assert_called_once_with(
                "command", "client 127.0.0.1:12345 set_expression smile"
            )

    @pytest.mark.asyncio
    async def test_set_motion(self, server):
        """モーション設定のテスト"""
        expected_response = {"status": "ok", "message": "Motion set"}

        with patch.object(
            server, "_send_ws_command", return_value=expected_response
        ) as mock_send:
            result = await server._set_motion("127.0.0.1:12345", "TapBody", 0, 2)
            assert result == expected_response
            mock_send.assert_called_once_with(
                "command", "client 127.0.0.1:12345 set_motion TapBody 0 2"
            )

    @pytest.mark.asyncio
    async def test_set_parameter(self, server):
        """パラメータ設定のテスト"""
        expected_response = {"status": "ok", "message": "Parameters set"}
        parameters = {"ParamAngleX": 10.0, "ParamEyeLOpen": 1.0}

        with patch.object(
            server, "_send_ws_command", return_value=expected_response
        ) as mock_send:
            result = await server._set_parameter("127.0.0.1:12345", parameters)
            assert result == expected_response
            # パラメータ文字列の検証（順序が異なる可能性があるため、部分一致で確認）
            call_args = mock_send.call_args[0]
            assert call_args[0] == "command"
            assert "client 127.0.0.1:12345 set_parameter" in call_args[1]
            assert "ParamAngleX=10.0" in call_args[1]
            assert "ParamEyeLOpen=1.0" in call_args[1]

    @pytest.mark.asyncio
    async def test_list_clients(self, server):
        """クライアント一覧取得のテスト"""
        expected_response = {
            "status": "ok",
            "clients": ["127.0.0.1:12345", "127.0.0.1:12346"],
        }

        with patch.object(
            server, "_send_ws_command", return_value=expected_response
        ) as mock_send:
            result = await server._list_clients()
            assert result == expected_response
            mock_send.assert_called_once_with("command", "list")

    @pytest.mark.asyncio
    async def test_set_eye_blink(self, server):
        """まばたき設定のテスト"""
        expected_response = {"status": "ok", "message": "Eye blink enabled"}

        with patch.object(
            server, "_send_ws_command", return_value=expected_response
        ) as mock_send:
            result = await server._set_eye_blink("127.0.0.1:12345", True)
            assert result == expected_response
            mock_send.assert_called_once_with(
                "command", "client 127.0.0.1:12345 set_eye_blink enabled"
            )

    @pytest.mark.asyncio
    async def test_set_breath(self, server):
        """呼吸設定のテスト"""
        expected_response = {"status": "ok", "message": "Breath disabled"}

        with patch.object(
            server, "_send_ws_command", return_value=expected_response
        ) as mock_send:
            result = await server._set_breath("127.0.0.1:12345", False)
            assert result == expected_response
            mock_send.assert_called_once_with(
                "command", "client 127.0.0.1:12345 set_breath disabled"
            )
