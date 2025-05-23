"""
WhatsApp Web Client

Main client class that orchestrates all WhatsApp Web functionality including
authentication, message handling, and WebSocket communication.
"""

import asyncio
import json
import logging
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path

from .websocket.handler import WebSocketHandler
from .auth.qr_auth import QRAuth
from .auth.session import Session
from .messages.processor import MessageProcessor, MessageEvent, MessageType
from .messages.media import MediaHandler
from .utils.logger import get_logger
from .utils.constants import WHATSAPP_WEB_VERSION, USER_AGENT


class WhatsAppClient:
    """
    Main WhatsApp Web client class.
    
    This class provides the primary interface for interacting with WhatsApp Web,
    including authentication, sending/receiving messages, and managing sessions.
    """

    def __init__(
        self,
        session_file: Optional[str] = None,
        browser_name: str = "WhatsApp Web Python",
        browser_version: str = "1.0.0"
    ):
        """
        Initialize WhatsApp Web client.

        Args:
            session_file: Path to session file for persistence
            browser_name: Browser name for user agent
            browser_version: Browser version for user agent
        """
        self.logger = get_logger(__name__)
        self.session_file = session_file or "session.json"
        self.browser_name = browser_name
        self.browser_version = browser_version
        
        # Core components
        self.session = Session()
        self.websocket_handler = WebSocketHandler()
        self.qr_auth = QRAuth()
        self.message_processor = MessageProcessor()
        self.media_handler = MediaHandler()
        
        # State management
        self.is_authenticated = False
        self.is_connected = False
        self.client_id: Optional[str] = None
        self.enc_key: Optional[bytes] = None
        self.mac_key: Optional[bytes] = None
        
        # Event handlers
        self.message_handlers: List[Callable[[MessageEvent], None]] = []
        self.connection_handlers: List[Callable[[bool], None]] = []
        self.qr_handlers: List[Callable[[str], None]] = []
        
        # Setup event handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup internal event handlers."""
        self.websocket_handler.on_message = self._handle_websocket_message
        self.websocket_handler.on_connection = self._handle_connection_change
        self.qr_auth.on_qr_code = self._handle_qr_code
        self.qr_auth.on_authenticated = self._handle_authentication

    async def start(self) -> bool:
        """
        Start the WhatsApp Web client.
        
        Returns:
            True if successfully started and authenticated
        """
        try:
            self.logger.info("Starting WhatsApp Web client...")
            
            # Try to restore existing session
            if await self._restore_session():
                self.logger.info("Session restored successfully")
                return await self._connect_with_session()
            
            # Start fresh authentication
            self.logger.info("Starting fresh authentication")
            return await self._start_fresh_auth()
            
        except Exception as e:
            self.logger.error(f"Failed to start client: {e}")
            return False

    async def _restore_session(self) -> bool:
        """Try to restore session from file."""
        try:
            if not Path(self.session_file).exists():
                return False
                
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
                
            if self.session.restore(session_data):
                self.client_id = session_data.get('clientId')
                self.enc_key = bytes.fromhex(session_data.get('encKey', ''))
                self.mac_key = bytes.fromhex(session_data.get('macKey', ''))
                return True
                
        except Exception as e:
            self.logger.warning(f"Failed to restore session: {e}")
            
        return False

    async def _connect_with_session(self) -> bool:
        """Connect using existing session."""
        try:
            # Connect WebSocket
            await self.websocket_handler.connect()
            
            # Send restore session request
            restore_message = {
                "action": "restore",
                "clientId": self.client_id,
                "serverToken": self.session.server_token,
                "clientToken": self.session.client_token
            }
            
            await self.websocket_handler.send_message(restore_message)
            
            # Wait for authentication confirmation
            # This would be handled by the message processor
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect with session: {e}")
            return False

    async def _start_fresh_auth(self) -> bool:
        """Start fresh authentication with QR code."""
        try:
            # Connect WebSocket
            await self.websocket_handler.connect()
            
            # Initialize QR authentication
            await self.qr_auth.initialize(
                self.websocket_handler,
                self.browser_name,
                self.browser_version
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start fresh authentication: {e}")
            return False

    async def _handle_websocket_message(self, message: Dict[str, Any]):
        """Handle incoming WebSocket messages."""
        try:
            # Process message through message processor
            events = await self.message_processor.process_message(
                message, 
                self.enc_key, 
                self.mac_key
            )
            
            # Emit events to handlers
            for event in events:
                for handler in self.message_handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(event)
                        else:
                            handler(event)
                    except Exception as e:
                        self.logger.error(f"Error in message handler: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error handling WebSocket message: {e}")

    async def _handle_connection_change(self, connected: bool):
        """Handle connection state changes."""
        self.is_connected = connected
        self.logger.info(f"Connection state changed: {connected}")
        
        for handler in self.connection_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(connected)
                else:
                    handler(connected)
            except Exception as e:
                self.logger.error(f"Error in connection handler: {e}")

    async def _handle_qr_code(self, qr_data: str):
        """Handle QR code generation."""
        self.logger.info("QR code generated")
        
        for handler in self.qr_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(qr_data)
                else:
                    handler(qr_data)
            except Exception as e:
                self.logger.error(f"Error in QR handler: {e}")

    async def _handle_authentication(self, auth_data: Dict[str, Any]):
        """Handle successful authentication."""
        try:
            # Extract authentication data
            self.client_id = auth_data.get('clientId')
            self.enc_key = auth_data.get('encKey')
            self.mac_key = auth_data.get('macKey')
            
            # Update session
            self.session.update_from_auth(auth_data)
            
            # Save session
            await self._save_session()
            
            self.is_authenticated = True
            self.logger.info("Authentication successful")
            
        except Exception as e:
            self.logger.error(f"Error handling authentication: {e}")

    async def _save_session(self):
        """Save current session to file."""
        try:
            session_data = {
                'clientId': self.client_id,
                'encKey': self.enc_key.hex() if self.enc_key else '',
                'macKey': self.mac_key.hex() if self.mac_key else '',
                'serverToken': self.session.server_token,
                'clientToken': self.session.client_token
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")

    async def send_text_message(self, jid: str, text: str) -> bool:
        """
        Send a text message.
        
        Args:
            jid: Recipient JID (WhatsApp ID)
            text: Message text
            
        Returns:
            True if message sent successfully
        """
        try:
            if not self.is_authenticated:
                raise Exception("Client not authenticated")
                
            message_data = {
                "type": "text",
                "to": jid,
                "body": text,
                "timestamp": int(asyncio.get_event_loop().time() * 1000)
            }
            
            # Encrypt and send message
            encrypted_message = await self.message_processor.encrypt_message(
                message_data, self.enc_key, self.mac_key
            )
            
            await self.websocket_handler.send_message(encrypted_message)
            
            self.logger.info(f"Text message sent to {jid}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send text message: {e}")
            return False

    async def send_media_message(
        self, 
        jid: str, 
        media_path: str, 
        media_type: str,
        caption: Optional[str] = None
    ) -> bool:
        """
        Send a media message.
        
        Args:
            jid: Recipient JID
            media_path: Path to media file
            media_type: Type of media (image, video, audio, document)
            caption: Optional caption
            
        Returns:
            True if message sent successfully
        """
        try:
            if not self.is_authenticated:
                raise Exception("Client not authenticated")
                
            # Upload media and get URL
            media_url = await self.media_handler.upload_media(
                media_path, media_type
            )
            
            message_data = {
                "type": media_type,
                "to": jid,
                "url": media_url,
                "caption": caption,
                "timestamp": int(asyncio.get_event_loop().time() * 1000)
            }
            
            # Encrypt and send message
            encrypted_message = await self.message_processor.encrypt_message(
                message_data, self.enc_key, self.mac_key
            )
            
            await self.websocket_handler.send_message(encrypted_message)
            
            self.logger.info(f"Media message sent to {jid}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send media message: {e}")
            return False

    def on_message(self, handler: Callable[[MessageEvent], None]):
        """Register message event handler."""
        self.message_handlers.append(handler)

    def on_connection(self, handler: Callable[[bool], None]):
        """Register connection event handler."""
        self.connection_handlers.append(handler)

    def on_qr_code(self, handler: Callable[[str], None]):
        """Register QR code event handler."""
        self.qr_handlers.append(handler)

    async def stop(self):
        """Stop the client and cleanup resources."""
        try:
            self.logger.info("Stopping WhatsApp Web client...")
            
            # Save session before stopping
            if self.is_authenticated:
                await self._save_session()
            
            # Disconnect WebSocket
            await self.websocket_handler.disconnect()
            
            # Reset state
            self.is_authenticated = False
            self.is_connected = False
            
            self.logger.info("Client stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping client: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
