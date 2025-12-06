"""Tests for the MCP server."""

import pytest

from acting_doll.server import list_tools


class TestServer:
    """Tests for the MCP server."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_tools(self) -> None:
        """Test that list_tools returns a list of tools."""
        tools = await list_tools()
        assert len(tools) == 6

    @pytest.mark.asyncio
    async def test_list_tools_contains_set_parameter(self) -> None:
        """Test that list_tools contains set_parameter tool."""
        tools = await list_tools()
        tool_names = [tool.name for tool in tools]
        assert "set_parameter" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_contains_set_expression(self) -> None:
        """Test that list_tools contains set_expression tool."""
        tools = await list_tools()
        tool_names = [tool.name for tool in tools]
        assert "set_expression" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_contains_start_motion(self) -> None:
        """Test that list_tools contains start_motion tool."""
        tools = await list_tools()
        tool_names = [tool.name for tool in tools]
        assert "start_motion" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_contains_get_model_info(self) -> None:
        """Test that list_tools contains get_model_info tool."""
        tools = await list_tools()
        tool_names = [tool.name for tool in tools]
        assert "get_model_info" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_contains_reset_pose(self) -> None:
        """Test that list_tools contains reset_pose tool."""
        tools = await list_tools()
        tool_names = [tool.name for tool in tools]
        assert "reset_pose" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_contains_set_look_at(self) -> None:
        """Test that list_tools contains set_look_at tool."""
        tools = await list_tools()
        tool_names = [tool.name for tool in tools]
        assert "set_look_at" in tool_names
