"""
AES Encryption Implementation

Implements AES encryption/decryption for WhatsApp Web's Signal Protocol.
Supports both AES-CBC and AES-GCM modes as used in different parts of the protocol.
"""

import os
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

from ..utils.logger import get_logger


class AESCipher:
    """
    AES encryption/decryption for WhatsApp Web.
    
    Handles both AES-CBC (with PKCS7 padding) and AES-GCM modes
    as used in different parts of the WhatsApp Web protocol.
    """

    def __init__(self):
        """Initialize AES cipher."""
        self.logger = get_logger(__name__)

    @staticmethod
    def encrypt_cbc(plaintext: bytes, key: bytes, iv: Optional[bytes] = None) -> bytes:
        """
        Encrypt data using AES-CBC with PKCS7 padding.
        
        Args:
            plaintext: Data to encrypt
            key: AES key (16, 24, or 32 bytes)
            iv: Initialization vector (16 bytes, random if None)
            
        Returns:
            IV + ciphertext
        """
        try:
            if iv is None:
                iv = os.urandom(16)
            elif len(iv) != 16:
                raise ValueError("IV must be 16 bytes")
                
            # Create padder
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(plaintext)
            padded_data += padder.finalize()
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=default_backend()
            )
            
            # Encrypt
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            
            # Return IV + ciphertext
            return iv + ciphertext
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"AES-CBC encryption failed: {e}")
            raise

    @staticmethod
    def decrypt_cbc(ciphertext: bytes, key: bytes) -> bytes:
        """
        Decrypt data using AES-CBC with PKCS7 padding.
        
        Args:
            ciphertext: IV + encrypted data
            key: AES key (16, 24, or 32 bytes)
            
        Returns:
            Decrypted plaintext
        """
        try:
            if len(ciphertext) < 16:
                raise ValueError("Ciphertext too short (need at least IV)")
                
            # Extract IV and ciphertext
            iv = ciphertext[:16]
            encrypted_data = ciphertext[16:]
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=default_backend()
            )
            
            # Decrypt
            decryptor = cipher.decryptor()
            padded_plaintext = decryptor.update(encrypted_data) + decryptor.finalize()
            
            # Remove padding
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext)
            plaintext += unpadder.finalize()
            
            return plaintext
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"AES-CBC decryption failed: {e}")
            raise

    @staticmethod
    def encrypt_gcm(plaintext: bytes, key: bytes, iv: Optional[bytes] = None, aad: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Encrypt data using AES-GCM.
        
        Args:
            plaintext: Data to encrypt
            key: AES key (16, 24, or 32 bytes)
            iv: Initialization vector (12 bytes recommended, random if None)
            aad: Additional authenticated data (optional)
            
        Returns:
            Tuple of (IV + ciphertext, authentication_tag)
        """
        try:
            if iv is None:
                iv = os.urandom(12)  # 96-bit IV for GCM
            elif len(iv) not in [12, 16]:
                raise ValueError("IV must be 12 or 16 bytes for GCM")
                
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv),
                backend=default_backend()
            )
            
            # Encrypt
            encryptor = cipher.encryptor()
            
            # Add AAD if provided
            if aad:
                encryptor.authenticate_additional_data(aad)
                
            ciphertext = encryptor.update(plaintext) + encryptor.finalize()
            
            # Get authentication tag
            tag = encryptor.tag
            
            return iv + ciphertext, tag
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"AES-GCM encryption failed: {e}")
            raise

    @staticmethod
    def decrypt_gcm(ciphertext: bytes, key: bytes, tag: bytes, aad: Optional[bytes] = None, iv_length: int = 12) -> bytes:
        """
        Decrypt data using AES-GCM.
        
        Args:
            ciphertext: IV + encrypted data
            key: AES key (16, 24, or 32 bytes)
            tag: Authentication tag
            aad: Additional authenticated data (optional)
            iv_length: Length of IV (12 or 16 bytes)
            
        Returns:
            Decrypted plaintext
        """
        try:
            if len(ciphertext) < iv_length:
                raise ValueError(f"Ciphertext too short (need at least {iv_length} bytes for IV)")
                
            # Extract IV and ciphertext
            iv = ciphertext[:iv_length]
            encrypted_data = ciphertext[iv_length:]
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            
            # Decrypt
            decryptor = cipher.decryptor()
            
            # Add AAD if provided
            if aad:
                decryptor.authenticate_additional_data(aad)
                
            plaintext = decryptor.update(encrypted_data) + decryptor.finalize()
            
            return plaintext
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"AES-GCM decryption failed: {e}")
            raise

    @staticmethod
    def encrypt_ctr(plaintext: bytes, key: bytes, nonce: Optional[bytes] = None) -> bytes:
        """
        Encrypt data using AES-CTR mode.
        
        Args:
            plaintext: Data to encrypt
            key: AES key (16, 24, or 32 bytes)
            nonce: Counter nonce (16 bytes, random if None)
            
        Returns:
            Nonce + ciphertext
        """
        try:
            if nonce is None:
                nonce = os.urandom(16)
            elif len(nonce) != 16:
                raise ValueError("Nonce must be 16 bytes")
                
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.CTR(nonce),
                backend=default_backend()
            )
            
            # Encrypt
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(plaintext) + encryptor.finalize()
            
            return nonce + ciphertext
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"AES-CTR encryption failed: {e}")
            raise

    @staticmethod
    def decrypt_ctr(ciphertext: bytes, key: bytes) -> bytes:
        """
        Decrypt data using AES-CTR mode.
        
        Args:
            ciphertext: Nonce + encrypted data
            key: AES key (16, 24, or 32 bytes)
            
        Returns:
            Decrypted plaintext
        """
        try:
            if len(ciphertext) < 16:
                raise ValueError("Ciphertext too short (need at least nonce)")
                
            # Extract nonce and ciphertext
            nonce = ciphertext[:16]
            encrypted_data = ciphertext[16:]
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.CTR(nonce),
                backend=default_backend()
            )
            
            # Decrypt
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(encrypted_data) + decryptor.finalize()
            
            return plaintext
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"AES-CTR decryption failed: {e}")
            raise

    @staticmethod
    def generate_key(key_size: int = 32) -> bytes:
        """
        Generate a random AES key.
        
        Args:
            key_size: Key size in bytes (16, 24, or 32)
            
        Returns:
            Random AES key
        """
        if key_size not in [16, 24, 32]:
            raise ValueError("Key size must be 16, 24, or 32 bytes")
            
        return os.urandom(key_size)

    @staticmethod
    def validate_key(key: bytes) -> bool:
        """
        Validate AES key.
        
        Args:
            key: Key to validate
            
        Returns:
            True if key is valid
        """
        return len(key) in [16, 24, 32]
