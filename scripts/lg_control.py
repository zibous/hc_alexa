import asyncio
import os
import argparse
import socket
from dotenv import load_dotenv
from aiowebostv import WebOsClient

# Lädt die Variablen aus der .env-Datei
load_dotenv()

LG_TV_IP = os.getenv("LG_TV_IP")
LG_TV_KEY = os.getenv("LG_TV_KEY")
LG_TV_MAC = os.getenv("LG_TV_MAC") # Neu: Wird für das Einschalten benötigt

def parse_arguments():
    parser = argparse.ArgumentParser(description="LG WebOS TV - CLI Steuerung (Dauerhafter Key)")
    parser.add_argument("--power", choices=["on", "off"], help="Fernseher ein- oder ausschalten.")
    parser.add_argument("--button", choices=["home", "back", "up", "down", "left", "right", "select", "volume_up", "volume_down", "mute"], help="Fernbedienungs-Taste drücken.")
    parser.add_argument("--app", help="App anhand des Namens starten (z.B. netflix, youtube).")
    parser.add_argument("--status", action="store_true", help="Status, aktuelle App und Lautstärke abfragen.")
    return parser.parse_args()

def send_wake_on_lan(mac_address: str):
    """Sendet ein standardisiertes WoL Magic Packet im Netzwerk, um den TV aufzuwecken."""
    if not mac_address:
        print("⚠️ Kann nicht einschalten: LG_TV_MAC fehlt in der .env-Datei!")
        return
        
    try:
        # MAC-Adresse bereinigen und in Bytes umwandeln
        clean_mac = mac_address.replace(":", "").replace("-", "")
        mac_bytes = bytes.fromhex(clean_mac)
        
        # Das Magic Packet besteht aus 6x FF gefolgt von 16x der MAC-Adresse
        packet = b'\xff' * 6 + mac_bytes * 16
        
        # Über UDP an den Broadcast senden
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(packet, ('255.255.255.255', 9))
            
        print(f"📡 Wake-on-LAN 'Magic Packet' an MAC {mac_address} gesendet!")
    except Exception as e:
        print(f"❌ Fehler beim Senden des Aufweck-Befehls: {e}")

async def main():
    if not LG_TV_IP:
        print("❌ Fehler: LG_TV_IP fehlt in der .env-Datei!")
        return

    args = parse_arguments()
    if not (args.power or args.button or args.app or args.status):
        print("ℹ️ Keine Befehle übergeben. Nutze --help für eine Übersicht.")
        return

    # --- SONDERFALL: TV AUFWECKEN WENN ER AUSGESCHALTET IST ---
    if args.power == "on":
        send_wake_on_lan(LG_TV_MAC)
        print("📺 Einschalt-Signal übertragen. Es kann bis zu 10 Sekunden dauern, bis das WLAN-Modul des TV hochgefahren ist.")
        return

    # Für alle anderen Befehle (Status, Aus, Tappen) muss der TV laufen.
    client_key_to_use = LG_TV_KEY if LG_TV_KEY else None
    client = WebOsClient(LG_TV_IP, client_key_to_use)

    print(f"🔄 Verbinde mit LG Fernseher ({LG_TV_IP})...")
    
    try:
        await client.connect()
    except Exception as e:
        print(f"❌ Verbindung fehlgeschlagen: {e}")
        print("   Stelle sicher, dass der TV eingeschaltet und im selben Netzwerk ist.")
        return

    # Falls wir ohne Key gestartet sind, fangen wir den vom TV generierten Schlüssel ab
    if client.client_key and client.client_key != LG_TV_KEY and not LG_TV_KEY:
        print(f"\n🔑 KOPPLUNG ERFOLGREICH!")
        print(f"Bitte füge diesen Schlüssel fest zu deiner .env-Datei hinzu:")
        print(f"LG_TV_KEY={client.client_key}\n")

    # --- ERWEITERTE STATUSABFRAGE ---
    if args.status:
        print("\n================ 📺 LG WEBOS TV STATUS ================")
        is_on = client.is_connected() if callable(getattr(client, 'is_connected', None)) else getattr(client, 'is_connected', False)
        print(f"   Eingeschaltet:       {is_on}")
        
        # Wartezeit für Datenübertragung erhöhen, damit der Tuner antworten kann
        await asyncio.sleep(0.8)
        
        # 1. Aktive App abfragen
        try:
            current_app = client.current_app_id
            if current_app:
                print(f"   Aktive App ID:       {current_app}")
            else:
                # 2. Falls keine App läuft, prüfen wir, ob Live-TV oder ein HDMI-Port aktiv ist
                current_input = await client.get_current_input()
                print(f"   Aktiver Eingang:     {current_input if current_input else 'Live-TV / Interner Tuner'}")
        except Exception:
            print("   Aktive App / Input:  Live-TV oder HDMI")

        # 3. Falls Live-TV läuft, versuchen wir den genauen Sendernamen auszulesen
        try:
            current_channel = await client.get_current_channel()
            if current_channel and "channelName" in current_channel:
                print(f"   Aktueller Sender:    {current_channel['channelName']} (Kanal {current_channel.get('channelNumber', '')})")
        except Exception:
            pass

        # 4. Lautstärke abfragen
        try:
            vol = client.volume
            muted = client.muted
            print(f"   Lautstärke:          {vol}% (Stumm: {muted})")
        except Exception:
            pass
            
        print("=======================================================")
        await client.disconnect()
        return

    # --- POWER STEUERN (NUR NOCH AUSSCHALTEN HIER) ---
    if args.power == "off":
        print("✍️ Schalte LG TV AUS...")
        await client.power_off()

    # --- TASTEN SIMULIEREN ---
    if args.button:
        key_mapping = {
            "home": "HOME", "back": "BACK", "up": "UP", "down": "DOWN", 
            "left": "LEFT", "right": "RIGHT", "select": "ENTER",
            "volume_up": "VOLUMEUP", "volume_down": "VOLUMEDOWN", "mute": "MUTE"
        }
        lg_key = key_mapping[args.button]
        print(f"✍️ Sende Tastendruck: {lg_key}...")
        await client.button(lg_key)

    # --- APPS STARTEN ---
    if args.app:
        print(f"🚀 Suche und starte App: {args.app}...")
        try:
            apps = client.apps
            target_app = None
            if apps:
                for app_id, app_info in apps.items():
                    if args.app.lower() in app_info.get("title", "").lower():
                        target_app = {"id": app_id, "title": app_info["title"]}
                        break
            if target_app:
                print(f"   Starte '{target_app['title']}' (ID: {target_app['id']})...")
                await client.launch_app(target_app["id"])
                print("   ✅ App-Startbefehl gesendet.")
            else:
                print(f"❌ App '{args.app}' wurde auf dem TV nicht gefunden.")
        except Exception as app_err:
            print(f"❌ Fehler beim App-Start: {app_err}")

    await client.disconnect()
    print("✅ Befehl ausgeführt.")

if __name__ == "__main__":
    asyncio.run(main())
