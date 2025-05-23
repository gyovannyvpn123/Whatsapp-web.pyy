"""
HKDF Implementation

Implements HKDF (HMAC-based Key Derivation Function) as specified in RFC 5869.
Used for key derivation in WhatsApp Web's Signal Protocol implementation.
"""

import hashlib
import hmac
from typing import Optional

from ..utils.logger import get_logger


class HKDF:
    """
    HKDF implementation for key derivation.
    
    Implements RFC 5869 HKDF using HMAC-SHA256 for WhatsApp Web's
    Signal Protocol key derivation requirements.
    """

    def __init__(self, hash_func=hashlib.sha256):
        """
        Initialize HKDF.
        
        Args:
            hash_func: Hash function to use (default: SHA-256)
        """
        self.logger = get_logger(__name__)
        self.hash_func = hash_func
        self.hash_len = hash_func().digest_size

    def extract(self, ikm: bytes, salt: Optional[bytes] = None) -> bytes:
        """
        HKDF Extract step.
        
        Args:
            ikm: Input keying material
            salt: Optional salt (if None, uses zero-filled string)
            
        Returns:
            Pseudo-random key (PRK)
        """
        try:
            if salt is None:
                salt = b'\x00' * self.hash_len
                
            # PRK = HMAC-Hash(salt, IKM)
            prk = hmac.new(salt, ikm, self.hash_func).digest()
            
            return prk
            
        except Exception as e:
            self.logger.error(f"HKDF extract failed: {e}")
            raise

    def expand(self, prk: bytes, length: int, info: Optional[bytes] = None) -> bytes:
        """
        HKDF Expand step.
        
        Args:
            prk: Pseudo-random key from extract step
            length: Length of output keying material in bytes
            info: Optional context and application specific information
            
        Returns:
            Output keying material (OKM)
        """
        try:
            if info is None:
                info = b''
                
            if length <= 0:
                raise ValueError("Length must be positive")
                
            if length > 255 * self.hash_len:
                raise ValueError("Length too large for HKDF")
                
            # Calculate number of iterations needed
            n = (length + self.hash_len - 1) // self.hash_len
            
            # Generate OKM
            okm = b''
            previous = b''
            
            for i in range(1, n + 1):
                # T(i) = HMAC-Hash(PRK, T(i-1) | info | i)
                data = previous + info + bytes([i])
                current = hmac.new(prk, data, self.hash_func).digest()
                okm += current
                previous = current
            
            # Return first 'length' bytes
            return okm[:length]
            
        except Exception as e:
            self.logger.error(f"HKDF expand failed: {e}")
            raise

    def derive(self, ikm: bytes, length: int, salt: Optional[bytes] = None, info: Optional[bytes] = None) -> bytes:
        """
        Complete HKDF key derivation (extract + expand).
        
        Args:
            ikm: Input keying material
            length: Length of output keying material in bytes
            salt: Optional salt
            info: Optional context information
            
        Returns:
            Derived key material
        """
        try:
            # Extract step
            prk = self.extract(ikm, salt)
            
            # Expand step
            okm = self.expand(prk, length, info)
            
            return okm
            
        except Exception as e:
            self.logger.error(f"HKDF derivation failed: {e}")
            raise

    @staticmethod
    def derive_whatsapp_keys(shared_secret: bytes, salt: bytes = b'') -> tuple:
        """
        Derive WhatsApp Web encryption and MAC keys from shared secret.
        
        Args:
            shared_secret: ECDH shared secret
            salt: Optional salt
            
        Returns:
            Tuple of (encryption_key, mac_key) - each 32 bytes
        """
        try:
            hkdf = HKDF()
            
            # Derive 64 bytes total (32 for encryption, 32 for MAC)
            derived_material = hkdf.derive(shared_secret, 64, salt)
            
            # Split into encryption and MAC keys
            encryption_key = derived_material[:32]
            mac_key = derived_material[32:]
            
            return encryption_key, mac_key
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"WhatsApp key derivation failed: {e}")
            raise

    @staticmethod
    def derive_session_keys(master_secret: bytes, handshake_hash: bytes) -> tuple:
        """
        Derive session keys for WhatsApp Web communication.
        
        Args:
            master_secret: Master secret from key exchange
            handshake_hash: Hash of handshake messages
            
        Returns:
            Tuple of (send_key, recv_key, send_mac_key, recv_mac_key)
        """
        try:
            hkdf = HKDF()
            
            # Derive session keys using handshake hash as info
            session_material = hkdf.derive(
                master_secret, 
                128,  # 32 bytes each for 4 keys
                info=handshake_hash
            )
            
            # Split into individual keys
            send_key = session_material[:32]
            recv_key = session_material[32:64]
            send_mac_key = session_material[64:96]
            recv_mac_key = session_material[96:128]
            
            return send_key, recv_key, send_mac_key, recv_mac_key
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Session key derivation failed: {e}")
            raise

    @staticmethod
    def derive_media_keys(media_key: bytes) -> tuple:
        """
        Derive media encryption keys for WhatsApp Web.
        
        Args:
            media_key: Base media key
            
        Returns:
            Tuple of (iv, cipher_key, mac_key)
        """
        try:
            hkdf = HKDF()
            
            # Derive keys for media encryption
            # WhatsApp uses specific info strings for different key types
            
            # Derive IV (16 bytes)
            iv = hkdf.derive(media_key, 16, info=b'WhatsApp Media Keys')[:16]
            
            # Derive cipher key (32 bytes)
            cipher_key = hkdf.derive(media_key, 32, info=b'WhatsApp Cipher Keys')
            
            # Derive MAC key (32 bytes)
            mac_key = hkdf.derive(media_key, 32, info=b'WhatsApp MAC Keys')
            
            return iv, cipher_key, mac_key
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Media key derivation failed: {e}")
            raise

    def verify_implementation(self) -> bool:
        """
        Verify HKDF implementation with test vectors.
        
        Returns:
            True if implementation is correct
        """
        try:
            # RFC 5869 Test Case 1
            ikm = bytes.fromhex('0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b')
            salt = bytes.fromhex('000102030405060708090a0b0c')
            info = bytes.fromhex('f0f1f2f3f4f5f6f7f8f9')
            length = 42
            
            expected_okm = bytes.fromhex(
                '3cb25f25faacd57a90434f64d0362f2a'
                '2d2d0a90cf1a5a4c5db02d56ecc4c5bf'
                '34007208d5b887185865'
            )
            
            # Test our implementation
            derived_okm = self.derive(ikm, length, salt, info)
            
            return derived_okm == expected_okm
            
        except Exception as e:
            self.logger.error(f"HKDF verification failed: {e}")
            return False
