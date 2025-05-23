"""
WebSocket message handler for WhatsApp Web protocol.
"""

import asyncio
from typing import Callable, Optional, Dict, Any
from ..utils.logger import get_logger
from ..protocol.binary_reader import BinaryReader
from ..protocol.binary_writer import BinaryWriter

logger = get_logger(__name__)

class WebSocketHandler:
    """Handles WebSocket messages and protocol communication."""
    
    def __init__(self):
        """Initialize WebSocket handler."""
        self.message_handlers: Dict[str, Callable] = {}
        self.binary_reader = BinaryReader()
        self.binary_writer = BinaryWriter()
        
    def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for specific message type."""
        self.message_handlers[message_type] = handler
        
    async def handle_message(self, raw_message: bytes):
        """Handle incoming WebSocket message."""
        try:
            # Parse binary message
            if isinstance(raw_message, str):
                # Text message
                await self._handle_text_message(raw_message)
            else:
                # Binary message
                await self._handle_binary_message(raw_message)
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _handle_text_message(self, message: str):
        """Handle text-based messages."""
        logger.debug(f"Received text message: {message}")
        
        # Handle connection establishment messages
        if "challenge" in message:
            await self._handle_challenge(message)
        elif "success" in message:
            await self._handle_success(message)
    
    async def _handle_binary_message(self, message: bytes):
        """Handle binary protocol messages."""
        try:
            # Decode binary message using WhatsApp protocol
            decoded = self.binary_reader.read_message(message)
            
            message_type = decoded.get('type', 'unknown')
            
            # Route to appropriate handler
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](decoded)
            else:
                logger.debug(f"Unhandled message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error decoding binary message: {e}")
    
    async def _handle_challenge(self, message: str):
        """Handle authentication challenge."""
        logger.info("Received authentication challenge")
        # Implementation for challenge response
        
    async def _handle_success(self, message: str):
        """Handle successful authentication."""
        logger.info("Authentication successful")
        # Implementation for success handling
    
    def create_binary_message(self, message_type: str, data: Dict[str, Any]) -> bytes:
        """Create binary message for sending."""
        return self.binary_writer.write_message(message_type, data)
