"""
Session management for WhatsApp Web authentication.
"""

import json
import os
from typing import Optional, Dict, Any
from pathlib import Path

class SessionManager:
    """Manages WhatsApp Web session data."""
    
    def __init__(self, session_file: str = "session.json"):
        """Initialize session manager."""
        self.session_file = session_file
        self.session_data = {}
        self.load_session()
    
    def load_session(self) -> bool:
        """Load session data from file."""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, "r") as f:
                    self.session_data = json.load(f)
                return True
        except Exception:
            pass
        return False
    
    def save_session(self, data: Dict[str, Any]):
        """Save session data to file."""
        self.session_data.update(data)
        with open(self.session_file, "w") as f:
            json.dump(self.session_data, f, indent=2)
    
    def get_session_data(self) -> Dict[str, Any]:
        """Get session data."""
        return self.session_data.copy()
    
    def clear_session(self):
        """Clear session data."""
        self.session_data = {}
        if os.path.exists(self.session_file):
            os.remove(self.session_file)
    
    def has_valid_session(self) -> bool:
        """Check if session is valid."""
        return bool(self.session_data.get('client_id') and 
                   self.session_data.get('server_token'))
