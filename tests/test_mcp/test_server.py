"""
Tests for Acting Doll MCP Server
"""
from unittest.mock import AsyncMock
import pytest

from adapter.server.handler_mcp import MCPServerHandler


class TestMCPServerHandler:
    """MCPサーバーのテストクラス"""

    @pytest.fixture
    def mock_handlers(self):
        """モックのコマンドハンドラーを作成"""
        return {
            "model_command": AsyncMock(),
            "client_command": AsyncMock(),
            "process_command": AsyncMock(),
        }

    @pytest.fixture
    def server(self, mock_handlers):
        """テスト用のサーバーインスタンスを作成"""
        return MCPServerHandler(
            model_command=mock_handlers["model_command"],
            client_command=mock_handlers["client_command"],
            process_command=mock_handlers["process_command"],
        )

    @pytest.mark.asyncio
    async def test_initialization(self, server):
        """初期化のテスト"""
        assert server.server is not None
        assert server.model_command is not None
        assert server.client_command is not None
        assert server.process_command is not None

    @pytest.mark.asyncio
    async def test_get_model_list(self, server, mock_handlers):
        """モデル一覧取得のテスト"""
        expected_response = {
            "status": "ok",
            "data": {"models": ["Haru", "Hiyori", "Mark"]},
        }
        mock_handlers["model_command"].return_value = expected_response

        result = await server._get_model_list()
        assert result == expected_response["data"]
        mock_handlers["model_command"].assert_called_once_with(
            "list", "", "mcp")

    @pytest.mark.asyncio
    async def test_get_model_info(self, server, mock_handlers):
        """モデル情報取得のテスト"""
        expressions_response = {"status": "ok",
                                "data": {"expressions": ["smile", "angry"]}}
        motions_response = {"status": "ok", "data": {
            "motions": {"TapBody": [0, 1, 2]}}}
        parameters_response = {
            "status": "ok",
            "data": {"parameters": ["ParamAngleX", "ParamAngleY"]},
        }

        mock_handlers["model_command"].side_effect = [
            expressions_response,
            motions_response,
            parameters_response,
        ]

        result = await server._get_model_info("Haru")
        assert result["model_name"] == "Haru"
        assert result["expressions"] == expressions_response["data"]
        assert result["motions"] == motions_response["data"]
        assert result["parameters"] == parameters_response["data"]

    @pytest.mark.asyncio
    async def test_set_expression(self, server, mock_handlers):
        """表情設定のテスト"""
        expected_response = {"status": "ok", "message": "Expression set"}
        mock_handlers["client_command"].return_value = expected_response

        result = await server._set_expression("127.0.0.1:12345", "smile")
        assert result == expected_response
        mock_handlers["client_command"].assert_called_once_with(
            "set_expression", "smile", "127.0.0.1:12345", "mcp"
        )

    @pytest.mark.asyncio
    async def test_set_motion(self, server, mock_handlers):
        """モーション設定のテスト"""
        expected_response = {"status": "ok", "message": "Motion set"}
        mock_handlers["client_command"].return_value = expected_response

        result = await server._set_motion("127.0.0.1:12345", "TapBody", 0, 2)
        assert result == expected_response
        mock_handlers["client_command"].assert_called_once_with(
            "set_motion", "TapBody 0 2", "127.0.0.1:12345", "mcp"
        )

    @pytest.mark.asyncio
    async def test_set_parameter(self, server, mock_handlers):
        """パラメータ設定のテスト"""
        expected_response = {"status": "ok", "message": "Parameters set"}
        parameters = {"ParamAngleX": 10.0, "ParamEyeLOpen": 1.0}
        mock_handlers["client_command"].return_value = expected_response

        result = await server._set_parameter("127.0.0.1:12345", parameters)
        assert result == expected_response
        mock_handlers["client_command"].assert_called_once_with(
            "set_parameter", parameters, "127.0.0.1:12345", "mcp"
        )

    @pytest.mark.asyncio
    async def test_list_clients(self, server, mock_handlers):
        """クライアント一覧取得のテスト"""
        expected_response = {
            "status": "ok",
            "data": {"clients": ["127.0.0.1:12345", "127.0.0.1:12346"]},
        }
        mock_handlers["process_command"].return_value = expected_response

        result = await server._list_clients()
        assert result == expected_response["data"]
        mock_handlers["process_command"].assert_called_once_with("list", "mcp")

    @pytest.mark.asyncio
    async def test_set_eye_blink(self, server, mock_handlers):
        """まばたき設定のテスト"""
        expected_response = {"status": "ok", "message": "Eye blink enabled"}
        mock_handlers["client_command"].return_value = expected_response

        result = await server._set_eye_blink("127.0.0.1:12345", True)
        assert result == expected_response
        mock_handlers["client_command"].assert_called_once_with(
            "set_eye_blink", "enabled", "127.0.0.1:12345", "mcp"
        )

    @pytest.mark.asyncio
    async def test_set_breath(self, server, mock_handlers):
        """呼吸設定のテスト"""
        expected_response = {"status": "ok", "message": "Breath disabled"}
        mock_handlers["client_command"].return_value = expected_response

        result = await server._set_breath("127.0.0.1:12345", False)
        assert result == expected_response
        mock_handlers["client_command"].assert_called_once_with(
            "set_breath", "disabled", "127.0.0.1:12345", "mcp"
        )
