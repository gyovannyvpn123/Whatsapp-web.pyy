"""
QR Code Authentication

Implements QR code generation and authentication flow for WhatsApp Web.
Handles the initial pairing process between client and WhatsApp servers.
"""

import asyncio
import base64
import json
import time
from typing import Optional, Callable, Dict, Any
import pyqrcode
from io import BytesIO
from PIL import Image

from ..crypto.curve import Curve25519
from ..crypto.hkdf import HKDF
from ..crypto.aes import AESCipher
from ..utils.logger import get_logger
from ..utils.constants import WHATSAPP_WEB_VERSION


class QRAuth:
    """
    Handles QR code authentication for WhatsApp Web.
    
    Manages the complete authentication flow from QR generation
    to key exchange and session establishment.
    """

    def __init__(self):
        """Initialize QR authentication handler."""
        self.logger = get_logger(__name__)
        
        # Authentication state
        self.client_id: Optional[str] = None
        self.private_key: Optional[bytes] = None
        self.public_key: Optional[bytes] = None
        self.qr_timeout = 30  # seconds
        
        # Event handlers
        self.on_qr_code: Optional[Callable[[str], None]] = None
        self.on_authenticated: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_timeout: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

    async def initialize(
        self, 
        websocket_handler, 
        browser_name: str, 
        browser_version: str
    ) -> bool:
        """
        Initialize authentication process.
        
        Args:
            websocket_handler: WebSocket handler instance
            browser_name: Browser name for handshake
            browser_version: Browser version for handshake
            
        Returns:
            True if initialization successful
        """
        try:
            self.logger.info("Initializing QR authentication...")
            
            # Generate client credentials
            self.client_id = Curve25519.generate_client_id()
            self.private_key, self.public_key = Curve25519.generate_keypair()
            
            # Send initialization message
            init_message = [
                "admin",
                "init",
                [2, 2121, 6],  # WhatsApp Web version info
                [browser_name, browser_version],
                self.client_id,
                True
            ]
            
            # Send initialization and wait for response
            response = await websocket_handler.send_message(
                init_message,
                wait_for_response=True,
                timeout=10.0
            )
            
            if response and 'data' in response:
                await self._handle_init_response(response['data'])
                return True
            else:
                raise Exception("Invalid initialization response")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize QR auth: {e}")
            if self.on_error:
                await self._safe_call_handler(self.on_error, e)
            return False

    async def _handle_init_response(self, response_data: Any):
        """Handle initialization response from server."""
        try:
            if isinstance(response_data, list) and len(response_data) >= 2:
                # Extract QR reference
                qr_ref = response_data[1] if len(response_data) > 1 else None
                
                if qr_ref:
                    await self._generate_qr_code(qr_ref)
                else:
                    raise Exception("No QR reference in response")
            else:
                raise Exception("Invalid response format")
                
        except Exception as e:
            self.logger.error(f"Error handling init response: {e}")
            raise

    async def _generate_qr_code(self, qr_ref: str):
        """
        Generate QR code for authentication.
        
        Args:
            qr_ref: QR reference from server
        """
        try:
            # Encode public key as base64
            public_key_b64 = base64.b64encode(self.public_key).decode('ascii')
            
            # Create QR data: ref,public_key,client_id
            qr_data = f"{qr_ref},{public_key_b64},{self.client_id}"
            
            self.logger.info("QR code generated successfully")
            
            # Notify QR handlers
            if self.on_qr_code:
                await self._safe_call_handler(self.on_qr_code, qr_data)
                
        except Exception as e:
            self.logger.error(f"Failed to generate QR code: {e}")
            raise

    def generate_qr_image(self, qr_data: str, scale: int = 8) -> bytes:
        """
        Generate QR code image.
        
        Args:
            qr_data: QR code data string
            scale: Scale factor for image size
            
        Returns:
            PNG image data as bytes
        """
        try:
            # Generate QR code
            qr = pyqrcode.create(qr_data)
            
            # Create PNG buffer
            png_buffer = BytesIO()
            qr.png(png_buffer, scale=scale)
            
            return png_buffer.getvalue()
            
        except Exception as e:
            self.logger.error(f"Failed to generate QR image: {e}")
            raise

    def get_qr_data_url(self, qr_data: str) -> str:
        """
        Generate QR code as data URL for web display.
        
        Args:
            qr_data: QR code data string
            
        Returns:
            Data URL string
        """
        try:
            png_data = self.generate_qr_image(qr_data)
            b64_data = base64.b64encode(png_data).decode('ascii')
            return f"data:image/png;base64,{b64_data}"
            
        except Exception as e:
            self.logger.error(f"Failed to generate QR data URL: {e}")
            raise

    async def handle_connection_message(self, message: Dict[str, Any]) -> bool:
        """
        Handle connection message from WhatsApp.
        
        Args:
            message: Connection message data
            
        Returns:
            True if authentication successful
        """
        try:
            if not isinstance(message, list) or len(message) < 2:
                return False
                
            if message[0] != "Conn":
                return False
                
            conn_data = message[1]
            if not isinstance(conn_data, dict) or 'secret' not in conn_data:
                return False
                
            # Decode shared secret
            shared_secret = base64.b64decode(conn_data['secret'])
            
            # Process authentication
            auth_data = await self._process_shared_secret(shared_secret)
            
            if auth_data:
                self.logger.info("Authentication successful")
                
                if self.on_authenticated:
                    await self._safe_call_handler(self.on_authenticated, auth_data)
                    
                return True
            else:
                raise Exception("Failed to process shared secret")
                
        except Exception as e:
            self.logger.error(f"Error handling connection message: {e}")
            if self.on_error:
                await self._safe_call_handler(self.on_error, e)
            return False

    async def _process_shared_secret(self, shared_secret: bytes) -> Optional[Dict[str, Any]]:
        """
        Process shared secret and derive session keys.
        
        Args:
            shared_secret: Shared secret from QR scan
            
        Returns:
            Authentication data dictionary
        """
        try:
            if len(shared_secret) < 96:  # 32 + 32 + 32 minimum
                raise ValueError("Shared secret too short")
                
            # Extract components from shared secret
            secret_public_key = shared_secret[:32]
            hmac_validation = shared_secret[32:64]
            encrypted_keys = shared_secret[64:]
            
            # Compute ECDH shared secret
            ecdh_secret = Curve25519.compute_shared_secret(
                self.private_key, 
                secret_public_key
            )
            
            # Derive keys using HKDF
            hkdf = HKDF()
            expanded_secret = hkdf.expand(ecdh_secret, 80)
            
            # Split expanded secret
            hmac_key = expanded_secret[32:64]
            aes_key = expanded_secret[:32]
            
            # Verify HMAC
            import hmac
            import hashlib
            
            expected_hmac = hmac.new(
                hmac_key,
                secret_public_key + encrypted_keys,
                hashlib.sha256
            ).digest()
            
            if not hmac.compare_digest(hmac_validation, expected_hmac):
                raise ValueError("HMAC validation failed")
                
            # Decrypt session keys
            aes_cipher = AESCipher()
            
            # Prepare ciphertext (add IV from expanded secret)
            iv = expanded_secret[64:][:16]
            ciphertext = iv + encrypted_keys
            
            decrypted_keys = aes_cipher.decrypt_cbc(ciphertext, aes_key)
            
            if len(decrypted_keys) < 64:
                raise ValueError("Decrypted keys too short")
                
            # Extract final keys
            enc_key = decrypted_keys[:32]
            mac_key = decrypted_keys[32:64]
            
            # Build authentication data
            auth_data = {
                'clientId': self.client_id,
                'encKey': enc_key,
                'macKey': mac_key,
                'serverToken': None,  # Will be provided later
                'clientToken': None,  # Will be generated
                'authenticated': True,
                'timestamp': int(time.time())
            }
            
            return auth_data
            
        except Exception as e:
            self.logger.error(f"Failed to process shared secret: {e}")
            return None

    async def start_timeout_monitor(self):
        """Start QR code timeout monitoring."""
        try:
            await asyncio.sleep(self.qr_timeout)
            
            self.logger.warning("QR code authentication timed out")
            
            if self.on_timeout:
                await self._safe_call_handler(self.on_timeout)
                
        except asyncio.CancelledError:
            # Timeout monitoring was cancelled (normal)
            pass
        except Exception as e:
            self.logger.error(f"Error in timeout monitor: {e}")

    async def _safe_call_handler(self, handler: Callable, *args):
        """Safely call event handler."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(*args)
            else:
                handler(*args)
        except Exception as e:
            self.logger.error(f"Error in event handler: {e}")

    def reset(self):
        """Reset authentication state."""
        self.client_id = None
        self.private_key = None
        self.public_key = None
        
        self.logger.info("QR authentication reset")

    def is_initialized(self) -> bool:
        """Check if authentication is initialized."""
        return (
            self.client_id is not None and 
            self.private_key is not None and 
            self.public_key is not None
        )

    def get_client_info(self) -> Dict[str, Any]:
        """
        Get client information.
        
        Returns:
            Dictionary with client info
        """
        return {
            'client_id': self.client_id,
            'has_keypair': self.private_key is not None,
            'initialized': self.is_initialized()
        }
