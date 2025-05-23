"""
Example Usage of WhatsApp Web Python Library

Demonstrates how to use the WhatsApp Web Python library for various
common tasks including authentication, sending messages, and handling events.
"""

import asyncio
import logging
import os
from pathlib import Path

from whatsapp_web_py import WhatsAppClient, MessageType, MessageEvent
from whatsapp_web_py.utils.logger import setup_logging


class WhatsAppBot:
    """Example WhatsApp bot implementation."""
    
    def __init__(self, session_file: str = "session.json"):
        """Initialize the bot."""
        self.session_file = session_file
        self.client = WhatsAppClient(
            session_file=session_file,
            browser_name="WhatsApp Bot",
            browser_version="1.0.0"
        )
        
        # Setup event handlers
        self.client.on_message(self.handle_message)
        self.client.on_connection(self.handle_connection)
        self.client.on_qr_code(self.handle_qr_code)
        
        # Bot state
        self.is_running = False

    def handle_qr_code(self, qr_data: str):
        """Handle QR code generation for authentication."""
        print("\n" + "="*50)
        print("QR CODE AUTHENTICATION REQUIRED")
        print("="*50)
        print("\nPlease scan the QR code below with WhatsApp:")
        print("\nQR Code Data:")
        print(qr_data)
        print("\nAlternatively, visit this URL to display the QR code:")
        print(f"http://localhost:5000/qr?data={qr_data}")
        print("\n" + "="*50)

    def handle_connection(self, connected: bool):
        """Handle connection state changes."""
        if connected:
            print("✅ Connected to WhatsApp Web!")
        else:
            print("❌ Disconnected from WhatsApp Web")

    async def handle_message(self, event: MessageEvent):
        """Handle incoming messages."""
        try:
            print(f"\n📨 New message from {event.jid}:")
            print(f"   Type: {event.type.value}")
            print(f"   From me: {event.from_me}")
            print(f"   Timestamp: {event.timestamp}")
            
            if event.type == MessageType.TEXT:
                text = event.content
                print(f"   Text: {text}")
                
                # Echo bot - reply to text messages
                if not event.from_me and text:
                    await self.handle_text_command(event.jid, text)
                    
            elif event.type == MessageType.IMAGE:
                print(f"   Image: {event.content.get('caption', 'No caption')}")
                
            elif event.type == MessageType.DOCUMENT:
                filename = event.content.get('fileName', 'Unknown')
                print(f"   Document: {filename}")
                
        except Exception as e:
            print(f"Error handling message: {e}")

    async def handle_text_command(self, jid: str, text: str):
        """Handle text commands from users."""
        text = text.strip().lower()
        
        try:
            if text == "/help":
                help_text = """
🤖 WhatsApp Bot Commands:

/help - Show this help message
/ping - Check if bot is responding
/echo <message> - Echo your message back
/info - Get bot information
/time - Get current time
/joke - Get a random joke
/quit - Stop the bot (admin only)
                """
                await self.client.send_text_message(jid, help_text.strip())
                
            elif text == "/ping":
                await self.client.send_text_message(jid, "🏓 Pong!")
                
            elif text.startswith("/echo "):
                echo_text = text[6:]  # Remove "/echo "
                await self.client.send_text_message(jid, f"📢 Echo: {echo_text}")
                
            elif text == "/info":
                info_text = f"""
ℹ️ Bot Information:
• Name: WhatsApp Bot
• Version: 1.0.0
• Status: Running
• Session: {self.session_file}
                """
                await self.client.send_text_message(jid, info_text.strip())
                
            elif text == "/time":
                import datetime
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await self.client.send_text_message(jid, f"🕐 Current time: {current_time}")
                
            elif text == "/joke":
                jokes = [
                    "Why don't scientists trust atoms? Because they make up everything!",
                    "Why did the scarecrow win an award? He was outstanding in his field!",
                    "Why don't eggs tell jokes? They'd crack each other up!",
                    "What do you call a fake noodle? An impasta!",
                    "Why did the math book look so sad? Because it had too many problems!"
                ]
                import random
                joke = random.choice(jokes)
                await self.client.send_text_message(jid, f"😄 {joke}")
                
            elif text == "/quit":
                # Only allow admin to quit (you can implement admin check)
                await self.client.send_text_message(jid, "👋 Goodbye! Bot shutting down...")
                self.is_running = False
                
            else:
                # Unknown command
                await self.client.send_text_message(
                    jid, 
                    "❓ Unknown command. Send /help to see available commands."
                )
                
        except Exception as e:
            print(f"Error handling command: {e}")
            await self.client.send_text_message(jid, "❌ Sorry, an error occurred processing your command.")

    async def start(self):
        """Start the bot."""
        print("🚀 Starting WhatsApp Bot...")
        
        # Start the client
        success = await self.client.start()
        
        if success:
            print("✅ Bot started successfully!")
            self.is_running = True
            
            # Keep the bot running
            try:
                while self.is_running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n⏹️ Bot stopped by user")
        else:
            print("❌ Failed to start bot")
            
        # Stop the client
        await self.client.stop()

    async def send_media_example(self, jid: str):
        """Example of sending media messages."""
        try:
            # Send an image
            image_path = "example_image.jpg"
            if Path(image_path).exists():
                success = await self.client.send_media_message(
                    jid, 
                    image_path, 
                    "image",
                    caption="Hello from WhatsApp Bot! 📸"
                )
                if success:
                    print("✅ Image sent successfully")
                else:
                    print("❌ Failed to send image")
            
            # Send a document
            doc_path = "example_document.pdf"
            if Path(doc_path).exists():
                success = await self.client.send_media_message(
                    jid, 
                    doc_path, 
                    "document",
                    caption="Here's a document for you 📄"
                )
                if success:
                    print("✅ Document sent successfully")
                else:
                    print("❌ Failed to send document")
                    
        except Exception as e:
            print(f"Error sending media: {e}")


async def basic_usage_example():
    """Basic usage example."""
    print("🔧 Basic Usage Example")
    print("=" * 30)
    
    # Create client
    client = WhatsAppClient(
        session_file="basic_session.json",
        browser_name="Basic Example",
        browser_version="1.0.0"
    )
    
    # Setup simple message handler
    def on_message(event: MessageEvent):
        print(f"Received message: {event.content}")
    
    def on_qr(qr_data: str):
        print(f"Scan QR: {qr_data}")
    
    client.on_message(on_message)
    client.on_qr_code(on_qr)
    
    try:
        # Start client
        async with client:
            print("✅ Client started, waiting for messages...")
            
            # Send a test message (replace with actual JID)
            # await client.send_text_message("1234567890@s.whatsapp.net", "Hello from Python!")
            
            # Wait for a bit
            await asyncio.sleep(10)
            
    except Exception as e:
        print(f"Error: {e}")


async def advanced_usage_example():
    """Advanced usage example with custom handlers."""
    print("⚡ Advanced Usage Example")
    print("=" * 30)
    
    client = WhatsAppClient(session_file="advanced_session.json")
    
    # Message statistics
    message_stats = {
        'total': 0,
        'text': 0,
        'media': 0,
        'sent': 0,
        'received': 0
    }
    
    async def message_handler(event: MessageEvent):
        """Advanced message handler with statistics."""
        message_stats['total'] += 1
        
        if event.from_me:
            message_stats['sent'] += 1
        else:
            message_stats['received'] += 1
            
        if event.type == MessageType.TEXT:
            message_stats['text'] += 1
        else:
            message_stats['media'] += 1
            
        # Log message details
        logging.info(f"Message processed: {event.type.value} from {event.jid}")
        
        # Print stats every 10 messages
        if message_stats['total'] % 10 == 0:
            print(f"📊 Message Statistics: {message_stats}")
    
    def connection_handler(connected: bool):
        """Connection handler."""
        status = "Connected" if connected else "Disconnected"
        print(f"🔗 Connection Status: {status}")
    
    # Register handlers
    client.on_message(message_handler)
    client.on_connection(connection_handler)
    
    try:
        # Start with context manager
        async with client:
            print("🚀 Advanced client started...")
            
            # Example of sending multiple message types
            test_jid = "1234567890@s.whatsapp.net"  # Replace with actual JID
            
            # Send text message
            # await client.send_text_message(test_jid, "Hello from advanced bot!")
            
            # Send media (if files exist)
            # await client.send_media_message(test_jid, "test.jpg", "image", "Test image")
            
            print("✅ Client running, press Ctrl+C to stop...")
            
            # Keep running until interrupted
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n⏹️ Shutting down...")
                
    except Exception as e:
        logging.error(f"Error in advanced example: {e}")


def main():
    """Main function to run examples."""
    # Setup logging
    setup_logging(
        level='INFO',
        log_file='whatsapp_bot.log'
    )
    
    print("🤖 WhatsApp Web Python Library Examples")
    print("=" * 50)
    print("\nChoose an example to run:")
    print("1. Basic Bot (interactive)")
    print("2. Basic Usage")
    print("3. Advanced Usage")
    print("4. Exit")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            # Interactive bot
            bot = WhatsAppBot()
            asyncio.run(bot.start())
            
        elif choice == "2":
            # Basic usage
            asyncio.run(basic_usage_example())
            
        elif choice == "3":
            # Advanced usage
            asyncio.run(advanced_usage_example())
            
        elif choice == "4":
            print("👋 Goodbye!")
            
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
