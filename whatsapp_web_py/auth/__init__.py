"""
Authentication module for WhatsApp Web login and session management.
"""

from .qr_auth import QRAuth
from .session import Session

__all__ = ["QRAuth", "Session"]
