"""
Acting Doll Server - WebSocket and MCP server for Live2D model control

This package provides a unified server that supports both WebSocket and MCP protocols
for controlling Live2D models through LLM interactions.
"""

__version__ = "0.1.0"
__author__ = "CodeneAria"

from .websocket_server import main, MCPServerHandler

__all__ = ["main", "MCPServerHandler", "__version__"]
