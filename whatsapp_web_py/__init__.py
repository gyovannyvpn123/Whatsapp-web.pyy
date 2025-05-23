"""
WhatsApp Web Python Library

A modern, complete Python library for WhatsApp Web based on verified reverse engineering.
Implements the full Signal Protocol encryption and WhatsApp Web protocol behavior.
"""

from .client import WhatsAppClient
from .auth.session import Session
from .messages.processor import MessageType, MessageEvent

__version__ = "1.0.0"
__author__ = "WhatsApp Web Python"
__email__ = "dev@whatsappwebpy.com"

__all__ = [
    "WhatsAppClient",
    "Session", 
    "MessageType",
    "MessageEvent"
]
