import asyncio
import os
import argparse
from dotenv import load_dotenv
from msmart.device import AirConditioner as AC_Device

# Lädt die Variablen aus der .env-Datei
load_dotenv()

DEVICE_IP = os.getenv("COMFEE_IP")
DEVICE_ID = os.getenv("COMFEE_ID")
DEVICE_TOKEN = os.getenv("COMFEE_TOKEN")
DEVICE_KEY = os.getenv("COMFEE_KEY")

def parse_arguments():
    """Definiert die Terminal-Parameter und die Hilfe-Texte."""
    parser = argparse.ArgumentParser(
        description="Comfee/Midea Klimaanlagen-Steuerung (All-in-One CLI)",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Hauptfunktionen
    parser.add_argument("--power", choices=["on", "off"], help="Klimaanlage ein- oder ausschalten.")
    parser.add_argument("--temp", type=int, choices=range(16, 31), metavar="[16-30]", help="Zieltemperatur in Grad Celsius festlegen.")
    parser.add_argument("--mode", choices=["auto", "cool", "dry", "heat", "fan"], help="Betriebsmodus wählen.")
    
    # Zusatzfunktionen (On / Off)
    parser.add_argument("--eco", choices=["on", "off"], help="Eco-Modus (Stromsparen) aktivieren oder deaktivieren.")
    parser.add_argument("--turbo", choices=["on", "off"], help="Turbo-Modus (Maximale Leistung) steuern.")
    parser.add_argument("--sleep", choices=["on", "off"], help="Sleep-Modus (Nachtmodus) steuern.")
    
    # Statusabfrage
    parser.add_argument("--status", action="store_true", help="Aktuellen Status und gemessene Temperaturen auslesen.")
    
    return parser.parse_args()

async def main():
    if not all([DEVICE_IP, DEVICE_ID, DEVICE_TOKEN, DEVICE_KEY]):
        print("❌ Fehler: Werte in der .env-Datei fehlen!")
        return

    args = parse_arguments()
    
    # Wenn überhaupt keine Argumente übergeben wurden, Hilfe anzeigen
    if not (args.power or args.temp or args.mode or args.eco or args.turbo or args.sleep or args.status):
        print("ℹ️ Keine Befehle übergeben. Nutze --help für eine Übersicht aller Befehle.")
        return

    print(f"🔄 Verbinde mit Klimaanlage ({DEVICE_IP})...")
    device = AC_Device(ip=DEVICE_IP, port=6444, device_id=int(DEVICE_ID))
    
    # Handshake & Status holen
    await device.authenticate(DEVICE_TOKEN, DEVICE_KEY)
    await device.refresh()
    
    # --- ERWEITERTE STATUSABFRAGE ---
    if args.status:
        print("\n================ 🌡️ AKTUELLER STATUS ================")
        print(f"  🟢 Betriebszustand")
        print(f"     Eingeschaltet:     {device.power_state}")
        print(f"     Betriebsmodus (ID): {device.operational_mode}")
        print(f"     Lüfterstufe:       {device.fan_speed}")
        
        print(f"\n  🌡️ Temperaturen")
        print(f"     Innentemperatur:   {device.indoor_temperature}°C")
        
        print(f"\n  ✨ Zusatzfunktionen")
        if hasattr(device, 'eco'):
            print(f"     Eco-Modus:         {device.eco}")
        if hasattr(device, 'turbo'):
            print(f"     Turbo-Modus:       {device.turbo}")
        if hasattr(device, 'sleep'):
            print(f"     Sleep-Modus:       {device.sleep}")
            
        print(f"\n  ⚠️ System & Diagnose")
        if hasattr(device, 'error_code'):
            print(f"     Fehlercode:        {device.error_code}")
        print("=====================================================")
        return

    # --- BEFEHLE VERARBEITEN ---
    has_changes = False

    # Power (An/Aus)
    if args.power is not None:
        new_power = True if args.power == "on" else False
        if device.power_state != new_power:
            device.power_state = new_power
            print(f"✍️ Ändere Power auf: {args.power.upper()}")
            has_changes = True

    # Temperatur (16-30)
    if args.temp is not None:
        if device.target_temperature != args.temp:
            device.target_temperature = args.temp
            print(f"✍️ Ändere Temperatur auf: {args.temp}°C")
            has_changes = True

    # Modus (Auto/Cool/etc.)
    if args.mode is not None:
        mode_mapping = {"auto": 1, "cool": 2, "dry": 3, "heat": 4, "fan": 5}
        target_mode_id = mode_mapping[args.mode]
        if device.operational_mode != target_mode_id:
            device.operational_mode = target_mode_id
            print(f"✍️ Ändere Modus auf: {args.mode.upper()}")
            has_changes = True

    # Eco-Modus (An/Aus)
    if args.eco is not None and hasattr(device, 'eco'):
        target_eco = True if args.eco == "on" else False
        if device.eco != target_eco:
            device.eco = target_eco
            print(f"✍️ Ändere Eco-Modus auf: {args.eco.upper()}")
            has_changes = True

    # Turbo-Modus (An/Aus)
    if args.turbo is not None and hasattr(device, 'turbo'):
        target_turbo = True if args.turbo == "on" else False
        if device.turbo != target_turbo:
            device.turbo = target_turbo
            print(f"✍️ Ändere Turbo-Modus auf: {args.turbo.upper()}")
            has_changes = True

    # Sleep-Modus (An/Aus)
    if args.sleep is not None and hasattr(device, 'sleep'):
        target_sleep = True if args.sleep == "on" else False
        if device.sleep != target_sleep:
            device.sleep = target_sleep
            print(f"✍️ Ändere Sleep-Modus auf: {args.sleep.upper()}")
            has_changes = True

    # --- BEFEHLE ABSENDEN ---
    if has_changes:
        print("🚀 Sende Änderungen an das Gerät...")
        try:
            await device.apply()
            print("✅ Erfolgreich aktualisiert!")
        except Exception as e:
            print(f"❌ Fehler beim Senden: {e}")
    else:
        print("ℹ️ Keine Änderungen notwendig (Werte entsprechen bereits dem Wunschzustand).")

if __name__ == "__main__":
    asyncio.run(main())
