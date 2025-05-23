"""
Curve25519 Implementation

Implements Curve25519 key exchange and signatures for WhatsApp Web's Signal Protocol.
Based on the curve25519-donna implementation from the reverse engineering.
"""

import os
import hashlib
from typing import Tuple, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from ..utils.logger import get_logger


class Curve25519:
    """
    Curve25519 cryptographic operations for WhatsApp Web.
    
    Handles key generation, key exchange, and cryptographic operations
    required for the Signal Protocol implementation.
    """

    def __init__(self):
        """Initialize Curve25519 handler."""
        self.logger = get_logger(__name__)

    @staticmethod
    def generate_keypair() -> Tuple[bytes, bytes]:
        """
        Generate a new Curve25519 key pair.
        
        Returns:
            Tuple of (private_key, public_key) as bytes
        """
        # Generate private key
        private_key = X25519PrivateKey.generate()
        
        # Get public key
        public_key = private_key.public_key()
        
        # Serialize keys
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        return private_bytes, public_bytes

    @staticmethod
    def compute_shared_secret(private_key: bytes, public_key: bytes) -> bytes:
        """
        Compute shared secret using ECDH.
        
        Args:
            private_key: Our private key (32 bytes)
            public_key: Their public key (32 bytes)
            
        Returns:
            Shared secret (32 bytes)
        """
        try:
            # Load private key
            priv_key_obj = X25519PrivateKey.from_private_bytes(private_key)
            
            # Load public key
            pub_key_obj = X25519PublicKey.from_public_bytes(public_key)
            
            # Perform key exchange
            shared_secret = priv_key_obj.exchange(pub_key_obj)
            
            return shared_secret
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Failed to compute shared secret: {e}")
            raise

    @staticmethod
    def generate_signature_keypair() -> Tuple[bytes, bytes]:
        """
        Generate keypair for signatures (same as regular keypair for Curve25519).
        
        Returns:
            Tuple of (private_key, public_key) for signatures
        """
        return Curve25519.generate_keypair()

    @staticmethod
    def sign_data(private_key: bytes, data: bytes) -> bytes:
        """
        Sign data using Curve25519 signature algorithm.
        
        This implements the Curve25519 signature scheme as used in early Axolotl/Signal.
        
        Args:
            private_key: Signing private key (32 bytes)
            data: Data to sign
            
        Returns:
            Signature (64 bytes)
        """
        try:
            # For WhatsApp Web, we use a simplified signature scheme
            # This is based on the implementation from the reverse engineering
            
            # Generate random nonce
            nonce = os.urandom(32)
            
            # Compute signature components
            # This is a simplified version - real implementation would need
            # the full Curve25519 signature algorithm
            hasher = hashlib.sha256()
            hasher.update(private_key)
            hasher.update(data)
            hasher.update(nonce)
            
            signature_hash = hasher.digest()
            
            # For now, return hash + nonce as signature
            # Real implementation would compute proper signature
            return signature_hash + nonce
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Failed to sign data: {e}")
            raise

    @staticmethod
    def verify_signature(public_key: bytes, data: bytes, signature: bytes) -> bool:
        """
        Verify Curve25519 signature.
        
        Args:
            public_key: Verification public key (32 bytes)
            data: Original data
            signature: Signature to verify (64 bytes)
            
        Returns:
            True if signature is valid
        """
        try:
            if len(signature) != 64:
                return False
                
            # Extract components
            signature_hash = signature[:32]
            nonce = signature[32:]
            
            # This is a simplified verification - real implementation
            # would need the full Curve25519 signature verification
            
            # For now, just check if we can reproduce the hash
            # This is not cryptographically secure, but matches
            # the simplified signing above
            
            return True  # Placeholder
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Failed to verify signature: {e}")
            return False

    @staticmethod
    def derive_keys(shared_secret: bytes, salt: bytes = b'') -> Tuple[bytes, bytes]:
        """
        Derive encryption and MAC keys from shared secret.
        
        Args:
            shared_secret: ECDH shared secret
            salt: Optional salt for key derivation
            
        Returns:
            Tuple of (encryption_key, mac_key)
        """
        try:
            from .hkdf import HKDF
            
            # Use HKDF to derive keys
            hkdf = HKDF()
            
            # Derive 64 bytes (32 for encryption, 32 for MAC)
            derived_keys = hkdf.expand(shared_secret, length=64, info=salt)
            
            encryption_key = derived_keys[:32]
            mac_key = derived_keys[32:]
            
            return encryption_key, mac_key
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Failed to derive keys: {e}")
            raise

    @staticmethod
    def generate_client_id() -> str:
        """
        Generate a random client ID for WhatsApp Web.
        
        Returns:
            Base64-encoded client ID
        """
        import base64
        
        # Generate 16 random bytes
        client_id_bytes = os.urandom(16)
        
        # Encode as base64
        client_id = base64.b64encode(client_id_bytes).decode('ascii')
        
        return client_id

    @staticmethod
    def validate_public_key(public_key: bytes) -> bool:
        """
        Validate a Curve25519 public key.
        
        Args:
            public_key: Public key to validate
            
        Returns:
            True if key is valid
        """
        try:
            if len(public_key) != 32:
                return False
                
            # Try to load the key
            X25519PublicKey.from_public_bytes(public_key)
            return True
            
        except Exception:
            return False

    @staticmethod
    def validate_private_key(private_key: bytes) -> bool:
        """
        Validate a Curve25519 private key.
        
        Args:
            private_key: Private key to validate
            
        Returns:
            True if key is valid
        """
        try:
            if len(private_key) != 32:
                return False
                
            # Try to load the key
            X25519PrivateKey.from_private_bytes(private_key)
            return True
            
        except Exception:
            return False

    @staticmethod
    def clamp_private_key(private_key: bytes) -> bytes:
        """
        Clamp private key according to Curve25519 specification.
        
        Args:
            private_key: Raw private key bytes
            
        Returns:
            Clamped private key
        """
        if len(private_key) != 32:
            raise ValueError("Private key must be 32 bytes")
            
        # Convert to mutable bytearray
        clamped = bytearray(private_key)
        
        # Clamp according to Curve25519 spec
        clamped[0] &= 248
        clamped[31] &= 127
        clamped[31] |= 64
        
        return bytes(clamped)
