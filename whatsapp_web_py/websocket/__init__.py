"""
WebSocket module for WhatsApp Web connection.
"""

from .connection import WebSocketConnection
from .handler import WebSocketHandler

__all__ = ["WebSocketConnection", "WebSocketHandler"]
