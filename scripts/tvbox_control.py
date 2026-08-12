import asyncio
import os
import argparse
import socket
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from androidtvremote2 import AndroidTVRemote, CannotConnect, ConnectionClosed, InvalidAuth

# Für die Zertifikatserstellung
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# Lädt die Variablen aus der .env-Datei
load_dotenv()

TVBOX_IP = os.getenv("TVBOX_IP")
SOUNDBAR_IP = os.getenv("SOUNDBAR_IP")

CERT_FILE = os.path.join(os.path.dirname(__file__), "cert.pem")
KEY_FILE = os.path.join(os.path.dirname(__file__), "key.pem")

def wake_soundbar_chain(ip: str):
    """Weckt die Soundbar mit einem rohen Netzwerk-Schubser auf den offenen HTTP-Port."""
    if not ip:
        print("⚠️ Kann Kette nicht starten: SOUNDBAR_IP fehlt in der .env-Datei!")
        return False
    
    print(f"🔌 Sende direkten HTTP-Weckruf an Soundbar ({ip}:8008)...")
    # Ein simpler, roher HTTP-Aufruf zwingt den Webserver der Soundbar, 
    # die Hardware aus dem Standby zu holen.
    raw_http_request = (
        "POST /apps/DefaultMediaReceiver HTTP/1.1\r\n"
        f"Host: {ip}:8008\r\n"
        "Content-Length: 0\r\n"
        "Connection: close\r\n\r\n"
    ).encode("utf-8")
    
    try:
        # Reines Python-Netzwerksocket – immun gegen Bibliotheks-Updates
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2.0)
            sock.connect((ip, 8008))
            sock.sendall(raw_http_request)
            # Kurz anlesen, um dem Gerät Zeit zur Verarbeitung zu geben
            try: sock.recv(1024)
            except Exception: pass
        print("🎵 Weckruf an Soundbar erfolgreich abgesetzt!")
        return True
    except Exception as e:
        print(f"⚠️ Soundbar-Weckruf fehlgeschlagen (Port blockiert?): {e}")
        return False

def generate_valid_google_certs():
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        print("🔑 Generiere professionelle Sicherheitszertifikate...")
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"Python-Server-Remote"),])
        cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(private_key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(datetime.now(timezone.utc) - timedelta(days=1)).not_valid_after(datetime.now(timezone.utc) + timedelta(days=3650)).sign(private_key, hashes.SHA256())
        with open(KEY_FILE, "wb") as f:
            f.write(private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=serialization.NoEncryption()))
        with open(CERT_FILE, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        print("✅ Zertifikate im korrekten Google-Format angelegt.")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Xiaomi TV Box S - Google Remote CLI")
    parser.add_argument("--power", choices=["on", "off"], help="Gezielt ein- oder ausschalten.")
    parser.add_argument("--button", choices=["home", "back", "up", "down", "left", "right", "select", "volume_up", "volume_down", "mute"], help="Fernbedienungs-Taste drücken.")
    parser.add_argument("--app", choices=["netflix", "youtube", "prime"], help="App direkt per DeepLink starten.")
    parser.add_argument("--text", type=str, help="Text direkt einfügen.")
    parser.add_argument("--status", action="store_true", help="Status abfragen.")
    return parser.parse_args()

def safe_disconnect(remote):
    if hasattr(remote, "disconnect"): remote.disconnect()

async def main():
    if not TVBOX_IP:
        print("❌ Fehler: TVBOX_IP fehlt in der .env-Datei!")
        return

    args = parse_arguments()
    if not (args.power or args.button or args.app or args.text or args.status):
        print("ℹ️ Keine Befehle übergeben. Nutze --help für eine Übersicht.")
        return

    # --- HDMI-CEC KALTSTART ---
    if args.power == "on":
        print("🔄 Starte HDMI-CEC Kaltstart-Sequenz über die Soundbar...")
        wake_soundbar_chain(SOUNDBAR_IP)
        print("⏳ Warte 5 Sekunden, bis TV und Box über HDMI hochgefahren sind...")
        await asyncio.sleep(5.0)

    generate_valid_google_certs()
    print(f"🔄 Verbinde mit Xiaomi TV Box ({TVBOX_IP})...")
    
    remote = AndroidTVRemote(host=TVBOX_IP, client_name="Python-Server-Remote", certfile=CERT_FILE, keyfile=KEY_FILE)
    
    try:
        await remote.async_connect()
    except (CannotConnect, InvalidAuth, Exception):
        if args.power == "on":
            print("⏳ Box braucht noch einen Moment. Letzter Verbindungsversuch...")
            await asyncio.sleep(3.0)
            try:
                await remote.async_connect()
            except Exception:
                print("❌ Verbindung fehlgeschlagen. Bitte prüfe, ob SimpLink/HDMI-CEC am LG TV eingeschaltet ist.")
                return
        else:
            print("\n🔑 Erstmalige Kopplung erforderlich! Die Box muss eingeschaltet sein.")
            return

    # --- STATUS ABFRAGE ---
    if args.status:
        print("\n================ 🖥️ XIAOMI TV BOX STATUS ================")
        print(f"   Eingeschaltet:       {remote.is_on}")
        await asyncio.sleep(0.4)
        current_app = getattr(remote, "current_app", None)
        if current_app:
            app_names = {"com.google.android.youtube.tv": "YouTube 📺", "com.netflix.ninja": "Netflix 🎬", "com.amazon.amazonvideo.livingroom": "Prime Video 🍿", "com.google.android.apps.tv.launcherx": "Google TV Startseite 🏠", "com.google.android.apps.tv.launcher": "Android TV Startseite 🏠"}
            print(f"   Aktive App:          {app_names.get(current_app, current_app)}")
        safe_disconnect(remote)
        return

    # --- POWER STEUREN ---
    if args.power:
        if args.power == "on" and not remote.is_on:
            print("✍️ Sende Power-Key an die Box...")
            await remote.async_send_key("POWER", "SHORT")
        elif args.power == "off" and remote.is_on:
            print("✍️ Schalte Box AUS...")
            await remote.async_send_key("POWER", "SHORT")

    # --- TEXT SENDEN ---
    if args.text:
        if hasattr(remote, "send_text"): remote.send_text(args.text)
        elif hasattr(remote, "async_send_text"): await remote.async_send_text(args.text)

    # --- TASTEN SIMULIEREN ---
    if args.button:
        key_name = args.button.upper()
        if key_name == "SELECT": key_name = "DPAD_CENTER"
        elif "DPAD_" not in key_name and key_name in ["UP", "DOWN", "LEFT", "RIGHT"]: key_name = f"DPAD_{key_name}"
        await remote.async_send_key(key_name, "SHORT")

    # --- APPS STARTEN ---
    if args.app:
        app_links = {"netflix": "https://netflix.com.*", "youtube": "https://youtube.com", "prime": "https://amazon.de"}
        await remote.async_send_app_link(app_links[args.app])

    safe_disconnect(remote)
    print("✅ Befehl ausgeführt.")

if __name__ == "__main__":
    asyncio.run(main())
