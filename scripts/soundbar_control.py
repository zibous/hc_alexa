import asyncio
import os
import argparse
import pychromecast
from dotenv import load_dotenv

# Lädt die Variablen aus der .env-Datei
load_dotenv()

SOUNDBAR_IP = os.getenv("SOUNDBAR_IP")

def parse_arguments():
    parser = argparse.ArgumentParser(description="LG Soundbar - Natives Google Cast Wecken")
    parser.add_argument("--power", choices=["on"], required=True, help="Soundbar via Cast einschalten.")
    return parser.parse_args()

def wake_lg_soundbar_via_cast(ip: str):
    print(f"📡 Starte Google Cast Gerätesuche für IP: {ip}...")
    browser = None
    try:
        chromecasts, browser = pychromecast.get_chromecasts()
        
        cast_device = None
        for cast in chromecasts:
            if hasattr(cast, "cast_info") and cast.cast_info and cast.cast_info.host == ip:
                cast_device = cast
                break
            elif hasattr(cast, "host") and cast.host == ip:
                cast_device = cast
                break
        
        if not cast_device:
            print(f"❌ Fehler: Kein Google Cast Gerät unter der IP {ip} im Netzwerk gefunden.")
            if browser:
                pychromecast.discovery.stop_discovery(browser)
            return False
            
        print(f"🎵 Gerät erfolgreich gefunden: '{cast_device.name}' (Modell: {cast_device.model_name})")
        print("🚀 Sende Weckruf (Starte Medien-Sitzung)...")
        
        cast_device.wait()
        
        # KORREKTUR: Feste App-ID für den Standard-Medienempfänger (Default Media Receiver)
        # Verhindert den 'get_app_id' Fehler komplett.
        cast_device.start_app("CC1AD845")
        print("✅ Google Cast Weckbefehl erfolgreich übertragen.")
        
        pychromecast.discovery.stop_discovery(browser)
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Google Cast Verbindung: {e}")
        if browser:
            try:
                pychromecast.discovery.stop_discovery(browser)
            except Exception:
                pass
        return False

async def main():
    if not SOUNDBAR_IP:
        print("❌ Fehler: SOUNDBAR_IP fehlt in der .env-Datei!")
        return

    args = parse_arguments()
    
    if args.power == "on":
        print(f"🔄 Starte native Cast-Wecksequenz für {SOUNDBAR_IP}...")
        
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(None, wake_lg_soundbar_via_cast, SOUNDBAR_IP)
        
        if success:
            print("📺 Die Soundbar fährt hoch und sollte den LG TV via HDMI SimpLink mit einschalten.")
        else:
            print("❌ Aufwecken fehlgeschlagen.")

if __name__ == "__main__":
    asyncio.run(main())
