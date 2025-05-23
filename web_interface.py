"""
Web Interface for WhatsApp Web Python Library

Provides a simple web interface for QR code display, session management,
and basic message monitoring using Flask.
"""

import asyncio
import json
import logging
import os
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.serving import make_server

from whatsapp_web_py import WhatsAppClient, MessageType, MessageEvent
from whatsapp_web_py.utils.logger import setup_logging
from whatsapp_web_py.auth.qr_auth import QRAuth


class WhatsAppWebInterface:
    """Web interface for WhatsApp Web Python library."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 5000):
        """Initialize web interface."""
        self.host = host
        self.port = port
        
        # Flask app
        self.app = Flask(__name__)
        self.app.secret_key = os.urandom(24)
        
        # WhatsApp client
        self.client: Optional[WhatsAppClient] = None
        self.client_thread: Optional[threading.Thread] = None
        self.client_loop: Optional[asyncio.AbstractEventLoop] = None
        
        # State management
        self.is_authenticated = False
        self.is_connected = False
        self.qr_data: Optional[str] = None
        self.current_status = "Disconnected"
        self.session_file = "web_session.json"
        
        # Message storage
        self.recent_messages: List[Dict[str, Any]] = []
        self.max_messages = 100
        
        # Setup routes
        self._setup_routes()
        
        # Setup logging
        setup_logging(level='INFO')
        self.logger = logging.getLogger(__name__)

    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main page."""
            return render_template('index.html', 
                                 authenticated=self.is_authenticated,
                                 connected=self.is_connected,
                                 status=self.current_status,
                                 qr_data=self.qr_data)
        
        @self.app.route('/api/status')
        def api_status():
            """Get current status."""
            return jsonify({
                'authenticated': self.is_authenticated,
                'connected': self.is_connected,
                'status': self.current_status,
                'has_qr': self.qr_data is not None,
                'message_count': len(self.recent_messages)
            })
        
        @self.app.route('/api/qr')
        def api_qr():
            """Get QR code data."""
            if self.qr_data:
                # Generate QR code image
                qr_auth = QRAuth()
                try:
                    qr_image_url = qr_auth.get_qr_data_url(self.qr_data)
                    return jsonify({
                        'qr_data': self.qr_data,
                        'qr_image': qr_image_url
                    })
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            else:
                return jsonify({'error': 'No QR code available'}), 404
        
        @self.app.route('/api/messages')
        def api_messages():
            """Get recent messages."""
            start = int(request.args.get('start', 0))
            limit = int(request.args.get('limit', 20))
            
            messages = self.recent_messages[start:start + limit]
            
            return jsonify({
                'messages': messages,
                'total': len(self.recent_messages),
                'start': start,
                'limit': limit
            })
        
        @self.app.route('/api/send_message', methods=['POST'])
        def api_send_message():
            """Send a message."""
            if not self.is_authenticated:
                return jsonify({'error': 'Not authenticated'}), 401
            
            data = request.get_json()
            jid = data.get('jid')
            message = data.get('message')
            
            if not jid or not message:
                return jsonify({'error': 'JID and message required'}), 400
            
            # Send message asynchronously
            if self.client and self.client_loop:
                future = asyncio.run_coroutine_threadsafe(
                    self.client.send_text_message(jid, message),
                    self.client_loop
                )
                
                try:
                    success = future.result(timeout=10)
                    if success:
                        return jsonify({'success': True, 'message': 'Message sent'})
                    else:
                        return jsonify({'error': 'Failed to send message'}), 500
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            else:
                return jsonify({'error': 'Client not available'}), 500
        
        @self.app.route('/api/connect', methods=['POST'])
        def api_connect():
            """Start WhatsApp connection."""
            if self.client_thread and self.client_thread.is_alive():
                return jsonify({'error': 'Already connecting/connected'}), 400
            
            # Start client in background thread
            self.client_thread = threading.Thread(target=self._run_client)
            self.client_thread.daemon = True
            self.client_thread.start()
            
            return jsonify({'success': True, 'message': 'Connection started'})
        
        @self.app.route('/api/disconnect', methods=['POST'])
        def api_disconnect():
            """Disconnect from WhatsApp."""
            if self.client and self.client_loop:
                # Stop client
                future = asyncio.run_coroutine_threadsafe(
                    self.client.stop(),
                    self.client_loop
                )
                
                try:
                    future.result(timeout=10)
                    self._reset_state()
                    return jsonify({'success': True, 'message': 'Disconnected'})
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            else:
                return jsonify({'error': 'Not connected'}), 400
        
        @self.app.route('/api/clear_session', methods=['POST'])
        def api_clear_session():
            """Clear saved session."""
            try:
                if os.path.exists(self.session_file):
                    os.remove(self.session_file)
                
                self._reset_state()
                
                return jsonify({'success': True, 'message': 'Session cleared'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    def _run_client(self):
        """Run WhatsApp client in background thread."""
        try:
            # Create new event loop for this thread
            self.client_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.client_loop)
            
            # Create client
            self.client = WhatsAppClient(
                session_file=self.session_file,
                browser_name="WhatsApp Web Interface",
                browser_version="1.0.0"
            )
            
            # Setup event handlers
            self.client.on_message(self._handle_message)
            self.client.on_connection(self._handle_connection)
            self.client.on_qr_code(self._handle_qr_code)
            
            # Run client
            self.client_loop.run_until_complete(self._client_main())
            
        except Exception as e:
            self.logger.error(f"Error in client thread: {e}")
            self.current_status = f"Error: {e}"
        finally:
            if self.client_loop:
                self.client_loop.close()
            self._reset_state()

    async def _client_main(self):
        """Main client coroutine."""
        try:
            self.current_status = "Connecting..."
            
            # Start client
            success = await self.client.start()
            
            if success:
                self.current_status = "Connected"
                
                # Keep running until stopped
                while self.client.is_connected or self.client.is_authenticated:
                    await asyncio.sleep(1)
            else:
                self.current_status = "Failed to connect"
                
        except Exception as e:
            self.logger.error(f"Error in client main: {e}")
            self.current_status = f"Error: {e}"

    async def _handle_message(self, event: MessageEvent):
        """Handle incoming messages."""
        try:
            # Format message for storage
            message_data = {
                'id': event.message_id,
                'jid': event.jid,
                'type': event.type.value,
                'timestamp': event.timestamp,
                'from_me': event.from_me,
                'content': self._format_message_content(event),
                'participant': event.participant,
                'datetime': datetime.fromtimestamp(event.timestamp).isoformat()
            }
            
            # Add to recent messages
            self.recent_messages.insert(0, message_data)
            
            # Limit message history
            if len(self.recent_messages) > self.max_messages:
                self.recent_messages = self.recent_messages[:self.max_messages]
                
            self.logger.info(f"Message received: {event.type.value} from {event.jid}")
            
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")

    def _format_message_content(self, event: MessageEvent) -> str:
        """Format message content for display."""
        if event.type == MessageType.TEXT:
            return str(event.content)
        elif event.type == MessageType.IMAGE:
            caption = event.content.get('caption', '') if isinstance(event.content, dict) else ''
            return f"📷 Image{': ' + caption if caption else ''}"
        elif event.type == MessageType.VIDEO:
            caption = event.content.get('caption', '') if isinstance(event.content, dict) else ''
            return f"🎥 Video{': ' + caption if caption else ''}"
        elif event.type == MessageType.AUDIO:
            return "🎵 Audio message"
        elif event.type == MessageType.DOCUMENT:
            filename = event.content.get('fileName', 'Document') if isinstance(event.content, dict) else 'Document'
            return f"📄 {filename}"
        elif event.type == MessageType.STICKER:
            return "🎭 Sticker"
        elif event.type == MessageType.LOCATION:
            return "📍 Location"
        elif event.type == MessageType.CONTACT:
            return "👤 Contact"
        else:
            return f"[{event.type.value}]"

    async def _handle_connection(self, connected: bool):
        """Handle connection state changes."""
        self.is_connected = connected
        
        if connected:
            self.current_status = "Connected"
            self.logger.info("Connected to WhatsApp Web")
        else:
            self.current_status = "Disconnected"
            self.logger.info("Disconnected from WhatsApp Web")

    async def _handle_qr_code(self, qr_data: str):
        """Handle QR code generation."""
        self.qr_data = qr_data
        self.current_status = "QR Code generated - Please scan"
        self.logger.info("QR code generated for authentication")

    def _reset_state(self):
        """Reset interface state."""
        self.is_authenticated = False
        self.is_connected = False
        self.qr_data = None
        self.current_status = "Disconnected"
        self.client = None
        self.client_loop = None

    def run(self, debug: bool = False):
        """Run the web interface."""
        print(f"🌐 Starting WhatsApp Web Interface on http://{self.host}:{self.port}")
        print("📱 Use this interface to:")
        print("   • Scan QR codes for authentication")
        print("   • Monitor incoming messages")
        print("   • Send test messages")
        print("   • Manage sessions")
        print("\n" + "="*60)
        
        try:
            # Create server
            server = make_server(self.host, self.port, self.app, threaded=True)
            
            print(f"✅ Server started successfully!")
            print(f"🔗 Open http://localhost:{self.port} in your browser")
            print("⏹️  Press Ctrl+C to stop")
            
            # Serve forever
            server.serve_forever()
            
        except KeyboardInterrupt:
            print("\n⏹️ Server stopped by user")
        except Exception as e:
            print(f"❌ Server error: {e}")
        finally:
            # Cleanup
            if self.client and self.client_loop:
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        self.client.stop(),
                        self.client_loop
                    )
                    future.result(timeout=5)
                except Exception as e:
                    print(f"Error stopping client: {e}")


def main():
    """Main function to run web interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description='WhatsApp Web Interface')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--session', default='web_session.json', help='Session file path')
    
    args = parser.parse_args()
    
    # Create and run interface
    interface = WhatsAppWebInterface(host=args.host, port=args.port)
    interface.session_file = args.session
    
    interface.run(debug=args.debug)


if __name__ == "__main__":
    main()
