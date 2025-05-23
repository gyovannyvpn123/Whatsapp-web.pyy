# WhatsApp Web Python Library

O bibliotecă Python modernă și completă pentru WhatsApp Web bazată pe reverse engineering verificat, cu implementare completă Signal Protocol și support async.

## 🚀 Caracteristici

### 📱 Mesagerie Completă
- ✅ **Mesaje text** - Trimite și primește mesaje cu formatare
- ✅ **Media rich** - Imagini, video, audio, documente, stickere, GIF-uri
- ✅ **Locații** - Coordonate GPS și locații partajate
- ✅ **Contacte** - Partajare vCard și informații contact
- ✅ **Link preview** - Metadata automat pentru link-uri
- ✅ **Reply și Quote** - Răspunde la mesaje specifice

### 👥 Gestionare Grupuri
- ✅ **Creare grupuri** - Creează și configurează grupuri noi
- ✅ **Gestionare membri** - Adaugă/elimină participanți
- ✅ **Permisiuni admin** - Gestionare drepturi și restricții
- ✅ **Metadata grup** - Schimbă nume, descriere, imagine
- ✅ **Invite links** - Generează și gestionează link-uri de invitație

### 🔐 Securitate și Autentificare
- ✅ **Signal Protocol** - Criptare end-to-end completă
- ✅ **QR Authentication** - Autentificare prin scanare QR
- ✅ **Session Management** - Gestionare automată sesiuni
- ✅ **Multi-device** - Support pentru multiple dispozitive

### 🌐 Interfață Web
- ✅ **Dashboard modern** - Interfață web responsivă
- ✅ **QR code display** - Afișare QR pentru autentificare
- ✅ **Message monitoring** - Monitorizare mesaje în timp real
- ✅ **Send interface** - Interfață pentru trimitere mesaje
- ✅ **Session management** - Control sesiuni prin web

## 📦 Instalare

### Cerințe
- Python 3.8+
- Dependențe în `requirements.txt`

### Setup Rapid
```bash
# Clonează repository-ul
git clone <your-repo-url>
cd whatsapp-web-python

# Instalează dependențele
pip install -r attached_assets/requirements.txt

# Rulează interfața web
python web_interface.py --host 0.0.0.0 --port 5000
```

### Dependențe Principale
```txt
websocket-client>=1.8.0
pycryptodome>=3.23.0
pyqrcode>=1.2.1
protobuf>=6.31.0
flask>=3.0.0
aiohttp>=3.10.0
cryptography>=43.0.0
```

## 🎯 Utilizare Rapidă

### 1. Bot Simplu
```python
import asyncio
from whatsapp_web_py import WhatsAppClient, MessageEvent

async def main():
    # Creează client
    client = WhatsAppClient(
        session_file="session.json",
        browser_name="My Bot",
        browser_version="1.0.0"
    )
    
    # Handler pentru mesaje
    async def on_message(event: MessageEvent):
        print(f"Mesaj de la {event.jid}: {event.content}")
        
        # Răspunde automat
        if not event.from_me and "hello" in event.content.lower():
            await client.send_text_message(event.jid, "Hello! 👋")
    
    # Handler pentru QR code
    def on_qr(qr_data: str):
        print(f"Scanează QR: {qr_data}")
    
    # Înregistrează handlerii
    client.on_message(on_message)
    client.on_qr_code(on_qr)
    
    # Pornește clientul
    async with client:
        print("Bot pornit! Apasă Ctrl+C pentru a opri.")
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Trimitere Media
```python
async def send_media_examples(client, jid):
    # Trimite imagine
    await client.send_media_message(
        jid=jid,
        file_path="imagine.jpg",
        media_type="image",
        caption="O imagine frumoasă! 📸"
    )
    
    # Trimite document
    await client.send_media_message(
        jid=jid,
        file_path="document.pdf",
        media_type="document",
        caption="Document important 📄"
    )
    
    # Trimite audio
    await client.send_media_message(
        jid=jid,
        file_path="audio.mp3",
        media_type="audio"
    )
```

### 3. Gestionare Grupuri
```python
async def group_management(client):
    # Creează grup
    group_jid = await client.create_group(
        name="Grupul Meu",
        participants=["1234567890@s.whatsapp.net", "0987654321@s.whatsapp.net"]
    )
    
    # Adaugă membri
    await client.add_group_participants(
        group_jid, 
        ["1111111111@s.whatsapp.net"]
    )
    
    # Schimbă numele grupului
    await client.update_group_name(group_jid, "Noul Nume")
    
    # Generează link de invitație
    invite_link = await client.get_group_invite_link(group_jid)
    print(f"Link invitație: {invite_link}")
```

## 🌐 Interfața Web

### Pornire Server Web
```bash
python web_interface.py --host 0.0.0.0 --port 5000
```

### Funcționalități Web Interface
- **Dashboard**: Status conexiune și statistici
- **QR Authentication**: Scanare QR pentru conectare
- **Message Center**: Vizualizare și trimitere mesaje
- **Session Manager**: Gestionare sesiuni salvate
- **Live Monitoring**: Monitorizare mesaje în timp real

### API Endpoints
```
GET  /                    - Dashboard principal
GET  /api/status         - Status conexiune
GET  /api/qr            - Date QR code
GET  /api/messages      - Lista mesaje recente
POST /api/send_message  - Trimite mesaj
POST /api/connect       - Pornește conexiunea
POST /api/disconnect    - Oprește conexiunea
POST /api/clear_session - Șterge sesiunea
```

## 🏗️ Arhitectura Proiectului

```
whatsapp_web_py/
├── __init__.py           # Main exports
├── client.py            # Client principal WhatsApp
├── auth/                # Autentificare și QR
│   ├── qr_auth.py      
│   └── session_manager.py
├── crypto/              # Criptografie și securitate
│   ├── curve.py        # Curve25519 implementation
│   ├── aes.py          # AES encryption
│   └── hkdf.py         # Key derivation
├── protocol/            # Protocol WhatsApp
│   ├── binary_reader.py
│   ├── binary_writer.py
│   └── constants.py
├── websocket/           # Comunicare WebSocket
│   ├── connection.py
│   └── handler.py
├── messages/            # Gestionare mesaje
│   ├── types.py
│   ├── handler.py
│   └── media.py
└── utils/               # Utilități
    ├── logger.py
    ├── helpers.py
    └── constants.py
```

## 🔧 Configurare Avansată

### Variables de Mediu
```bash
export WHATSAPP_SESSION_FILE="custom_session.json"
export WHATSAPP_LOG_LEVEL="DEBUG"
export WHATSAPP_LOG_FILE="whatsapp.log"
export WHATSAPP_BROWSER_NAME="Custom Browser"
```

### Configurare Custom
```python
from whatsapp_web_py import WhatsAppClient
from whatsapp_web_py.utils.logger import setup_logging

# Setup logging personalizat
setup_logging(
    level='DEBUG',
    log_file='bot.log',
    format_string='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Client cu configurare custom
client = WhatsAppClient(
    session_file="my_session.json",
    browser_name="Custom WhatsApp Bot",
    browser_version="2.0.0",
    auto_reconnect=True,
    max_reconnect_attempts=10,
    keepalive_interval=30
)
```

## 📚 Exemple Complete

### Bot Echo Inteligent
```python
import asyncio
from whatsapp_web_py import WhatsAppClient, MessageType, MessageEvent

class EchoBot:
    def __init__(self):
        self.client = WhatsAppClient(session_file="echo_session.json")
        self.client.on_message(self.handle_message)
        self.client.on_qr_code(self.handle_qr)
        
    async def handle_message(self, event: MessageEvent):
        if event.from_me:
            return  # Ignoră mesajele trimise de bot
            
        if event.type == MessageType.TEXT:
            text = event.content.lower()
            
            if text.startswith("/echo "):
                response = text[6:]  # Remove "/echo "
                await self.client.send_text_message(
                    event.jid, 
                    f"Echo: {response}"
                )
            elif text == "/help":
                help_text = """
🤖 Echo Bot Commands:
/echo <message> - Echo your message
/help - Show this help
                """
                await self.client.send_text_message(event.jid, help_text)
                
    def handle_qr(self, qr_data: str):
        print(f"Scanează QR: {qr_data}")
        
    async def start(self):
        async with self.client:
            print("Echo Bot started!")
            await asyncio.Event().wait()

# Rulează bot
bot = EchoBot()
asyncio.run(bot.start())
```

### Media Bot Avansat
```python
import asyncio
import os
from pathlib import Path
from whatsapp_web_py import WhatsAppClient, MessageType, MessageEvent

class MediaBot:
    def __init__(self):
        self.client = WhatsAppClient(session_file="media_session.json")
        self.client.on_message(self.handle_message)
        
    async def handle_message(self, event: MessageEvent):
        if event.from_me:
            return
            
        if event.type == MessageType.TEXT:
            command = event.content.lower().strip()
            
            if command == "/photo":
                await self.send_sample_photo(event.jid)
            elif command == "/document":
                await self.send_sample_document(event.jid)
            elif command == "/audio":
                await self.send_sample_audio(event.jid)
                
        elif event.type == MessageType.IMAGE:
            # Răspunde la imagini primite
            await self.client.send_text_message(
                event.jid,
                "Imagine frumoasă! 📸 Mulțumesc pentru partajare!"
            )
            
    async def send_sample_photo(self, jid):
        if Path("sample.jpg").exists():
            await self.client.send_media_message(
                jid=jid,
                file_path="sample.jpg",
                media_type="image",
                caption="Iată o imagine sample! 📷"
            )
        else:
            await self.client.send_text_message(
                jid, 
                "Nu am găsit imaginea sample.jpg"
            )
            
    async def send_sample_document(self, jid):
        if Path("document.pdf").exists():
            await self.client.send_media_message(
                jid=jid,
                file_path="document.pdf",
                media_type="document",
                caption="Document important 📄"
            )
            
    async def send_sample_audio(self, jid):
        if Path("audio.mp3").exists():
            await self.client.send_media_message(
                jid=jid,
                file_path="audio.mp3",
                media_type="audio"
            )

# Rulează media bot
media_bot = MediaBot()
asyncio.run(media_bot.start())
```

## 🐛 Debugging și Troubleshooting

### Activare Debug Logging
```python
from whatsapp_web_py.utils.logger import enable_debug_logging
enable_debug_logging()
```

### Probleme Comune

#### 1. Conexiune eșuată
```python
# Verifică conectivitatea
import socket
try:
    socket.gethostbyname('w1.web.whatsapp.net')
    print("✅ DNS funcționează")
except:
    print("❌ Problemă DNS/conectivitate")
```

#### 2. QR Code nu se generează
```python
# Verifică sesiunea
import os
if os.path.exists("session.json"):
    os.remove("session.json")  # Șterge sesiunea veche
    print("Sesiune ștearsă, încearcă din nou")
```

#### 3. Mesaje nu se trimit
```python
# Verifică formatul JID
from whatsapp_web_py.utils.helpers import validate_jid
jid = "1234567890@s.whatsapp.net"
if validate_jid(jid):
    print("✅ JID valid")
else:
    print("❌ JID invalid")
```

## 🤝 Contribuții

### Development Setup
```bash
# Clone repo
git clone <repo-url>
cd whatsapp-web-python

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Format code
black whatsapp_web_py/
isort whatsapp_web_py/
```

### Guidelines
1. **Code Style**: Folosește Black și isort pentru formatare
2. **Type Hints**: Adaugă type hints pentru toate funcțiile
3. **Documentation**: Documentează funcțiile și clasele noi
4. **Tests**: Scrie teste pentru funcționalități noi
5. **Commit Messages**: Folosește conventional commits

## 📄 Licență

Acest proiect este licențiat sub MIT License - vezi fișierul [LICENSE](LICENSE) pentru detalii.

## 🙏 Recunoașteri

- **whatsapp-web-reveng** - Reverse engineering original de sigalor
- **Signal Protocol** - Implementare criptografie end-to-end
- **WhatsApp Inc.** - Pentru protocolul original (reverse engineered)

## ⚠️ Disclaimer

Această bibliotecă este creată în scopuri educaționale și de cercetare. Utilizarea sa trebuie să respecte Terms of Service ale WhatsApp. Autorii nu sunt responsabili pentru utilizarea necorespunzătoare.

---

**Creat cu ❤️ pentru comunitatea Python și reverse engineering**

📧 Pentru întrebări sau suport, deschide un issue pe GitHub.