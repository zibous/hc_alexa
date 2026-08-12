import asyncio
import os
import argparse
from dotenv import load_dotenv
from miio import AirPurifierMiot

# Lädt die Variablen aus der .env-Datei
load_dotenv()

PURIFIER_IP = os.getenv("PURIFIER_IP")
PURIFIER_TOKEN = os.getenv("PURIFIER_TOKEN")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Xiaomi Air Purifier Steuerung - Profi-Modus")
    parser.add_argument("--power", choices=["on", "off"], help="Luftreiniger ein- oder ausschalten.")
    parser.add_argument("--mode", choices=["auto", "silent", "favorite"], help="Modus wählen.")
    parser.add_argument("--status", action="store_true", help="Alle Sensoren und erweiterten Status anzeigen.")
    return parser.parse_args()

async def main():
    if not PURIFIER_IP or not PURIFIER_TOKEN:
        print("❌ Fehler: PURIFIER_IP oder PURIFIER_TOKEN fehlt in der .env-Datei!")
        return

    args = parse_arguments()
    if not (args.power or args.mode or args.status):
        print("ℹ️ Keine Befehle übergeben. Nutze --help für eine Übersicht.")
        return

    print(f"🔄 Verbinde mit Luftreiniger ({PURIFIER_IP})...")
    purifier = AirPurifierMiot(ip=PURIFIER_IP, token=PURIFIER_TOKEN)
    loop = asyncio.get_event_loop()

    # --- SENSORIK & DETAILS AUSLESEN ---
    if args.status:
        status = await loop.run_in_executor(None, purifier.status)
        print("\n=================== 🍃 LUFTREINIGER DETAIL-STATUS ===================")
        
        print("  🟢 Betriebszustand")
        print(f"     Eingeschaltet:       {status.is_on}")
        print(f"     Aktueller Modus:     {status.mode}")
        
        print("\n  📊 Raumklima & Sensoren")
        if hasattr(status, 'aqi') and status.aqi is not None:
            print(f"     Luftqualität (PM2.5): {status.aqi} µg/m³")
        
        # Temperatur-Prüfung repariert (verhindert den None-Absturz)
        if hasattr(status, 'temperature') and status.temperature is not None:
            print(f"     Raumtemperatur:      {status.temperature:.1f}°C")
        else:
            print("     Raumtemperatur:      Nicht verfügbar")
            
        if hasattr(status, 'humidity') and status.humidity is not None:
            print(f"     Luftfeuchtigkeit:    {status.humidity}%")
            
        print("\n  📦 Filter-Informationen")
        if hasattr(status, 'filter_life_level') and status.filter_life_level is not None:
            print(f"     Filter-Lebensdauer:  {status.filter_life_level}%")
            
        try:
            if hasattr(status, 'filter_hours_used') and status.filter_hours_used is not None:
                print(f"     Betriebsstunden:     {status.filter_hours_used} Std.")
        except Exception:
            pass

        print("\n  ⚙️ Display & Hardware-Einstellungen")
        try:
            if hasattr(status, 'led') and status.led is not None:
                print(f"     Display an:          {status.led}")
            if hasattr(status, 'child_lock') and status.child_lock is not None:
                print(f"     Kindersicherung:     {status.child_lock}")
            if hasattr(status, 'buzzer') and status.buzzer is not None:
                print(f"     Tonsignale (Buzzer): {status.buzzer}")
        except Exception:
            print("     Zusatz-Hardwareinfos konnten nicht voll ausgelesen werden.")

        print("=====================================================================")
        return

    # --- BEFEHLE ---
    if args.power is not None:
        if args.power == "on":
            print("✍️ Schalte Luftreiniger EIN...")
            await loop.run_in_executor(None, purifier.on)
        else:
            print("✍️ Schalte Luftreiniger AUS...")
            await loop.run_in_executor(None, purifier.off)
        print("✅ Erfolgreich geschaltet!")

    if args.mode is not None:
        print(f"✍️ Ändere Modus auf: {args.mode.upper()}")
        await loop.run_in_executor(None, purifier.set_mode, args.mode)
        print("✅ Modus erfolgreich geändert!")

if __name__ == "__main__":
    asyncio.run(main())
