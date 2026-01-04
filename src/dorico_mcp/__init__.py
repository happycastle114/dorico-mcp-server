"""
Dorico MCP Server - Control Dorico via Claude Desktop

A Model Context Protocol (MCP) server that enables natural language control
of Steinberg Dorico music notation software through Claude Desktop.

Designed as a gift for composition majors (작곡 전공자).
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from dorico_mcp.client import DoricoClient
from dorico_mcp.server import create_server

__all__ = ["DoricoClient", "create_server", "__version__"]
