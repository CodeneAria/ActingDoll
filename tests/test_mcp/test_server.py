"""Tests for the MCP server."""

import pytest

from acting_doll.server import list_tools


class TestServer:
    """Tests for the MCP server."""

    @pytest.fixture
    async def tools_list(self):
        """Get the list of tools once for all tests."""
        return await list_tools()

    @pytest.mark.asyncio
    async def test_list_tools_returns_tools(self, tools_list) -> None:
        """Test that list_tools returns a list of tools."""
        assert len(tools_list) == 6

    @pytest.mark.asyncio
    async def test_list_tools_contains_set_parameter(self, tools_list) -> None:
        """Test that list_tools contains set_parameter tool."""
        tool_names = [tool.name for tool in tools_list]
        assert "set_parameter" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_contains_set_expression(self, tools_list) -> None:
        """Test that list_tools contains set_expression tool."""
        tool_names = [tool.name for tool in tools_list]
        assert "set_expression" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_contains_start_motion(self, tools_list) -> None:
        """Test that list_tools contains start_motion tool."""
        tool_names = [tool.name for tool in tools_list]
        assert "start_motion" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_contains_get_model_info(self, tools_list) -> None:
        """Test that list_tools contains get_model_info tool."""
        tool_names = [tool.name for tool in tools_list]
        assert "get_model_info" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_contains_reset_pose(self, tools_list) -> None:
        """Test that list_tools contains reset_pose tool."""
        tool_names = [tool.name for tool in tools_list]
        assert "reset_pose" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_contains_set_look_at(self, tools_list) -> None:
        """Test that list_tools contains set_look_at tool."""
        tool_names = [tool.name for tool in tools_list]
        assert "set_look_at" in tool_names
