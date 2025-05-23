"""
WebSocket connection management for WhatsApp Web.
"""

import asyncio
import websockets
import ssl
from typing import Optional, Callable, Any
from ..utils.logger import get_logger

logger = get_logger(__name__)

class WebSocketConnection:
    """Manages WebSocket connection to WhatsApp Web servers."""
    
    def __init__(self, url: str = "wss://w1.web.whatsapp.net/ws/chat"):
        """Initialize WebSocket connection."""
        self.url = url
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        self.on_message: Optional[Callable] = None
        self.on_close: Optional[Callable] = None
        
    async def connect(self, headers: dict = None) -> bool:
        """Connect to WhatsApp Web servers."""
        try:
            logger.info(f"Connecting to {self.url}")
            
            # Default headers
            default_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Origin': 'https://web.whatsapp.com'
            }
            
            if headers:
                default_headers.update(headers)
            
            # Connect with SSL
            ssl_context = ssl._create_unverified_context()
            
            self.websocket = await websockets.connect(
                self.url,
                extra_headers=default_headers,
                ssl=ssl_context,
                timeout=10
            )
            
            self.is_connected = True
            logger.info("WebSocket connection established")
            
            # Start message loop
            asyncio.create_task(self._message_loop())
            
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.is_connected = False
            return False
    
    async def send(self, data: bytes):
        """Send data through WebSocket."""
        if self.websocket and self.is_connected:
            await self.websocket.send(data)
        else:
            raise Exception("WebSocket not connected")
    
    async def close(self):
        """Close WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("WebSocket connection closed")
    
    async def _message_loop(self):
        """Handle incoming messages."""
        try:
            async for message in self.websocket:
                if self.on_message:
                    await self.on_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed by server")
            self.is_connected = False
            if self.on_close:
                await self.on_close()
        except Exception as e:
            logger.error(f"Message loop error: {e}")
            self.is_connected = False
