"""
Acting Doll Server - WebSocket and MCP server for Live2D model control

This package provides a unified server that supports both WebSocket and MCP protocols
for controlling Live2D models through LLM interactions.
"""

__version__ = "0.2.0"
__author__ = "CodeneAria"

from acting_doll_server import run_acting_doll

__all__ = ["run_acting_doll"]
