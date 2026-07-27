from app.core.device_loader import load_devices
from app.processor.handlers.discovery import DiscoveryHandler
from app.processor.handlers.control import ControlHandler
from app.processor.handlers.state import StateHandler

class AlexaProcessor:
    def __init__(self):
        self.discovery_handler = DiscoveryHandler()
        self.control_handler = ControlHandler()
        self.state_handler = StateHandler()

    async def process_request(self, payload: dict) -> dict:
        directive = payload.get("directive", {})
        header = directive.get("header", {})
        namespace = header.get("namespace")
        
        devices = load_devices()

        # 1. Geräte-Erkennung
        if namespace == "Alexa.Discovery":
            return self.discovery_handler.handle(devices, header)

        # 2. Statusabfragen (z.B. Temperatursensor)
        if namespace == "Alexa" and header.get("name") == "ReportState":
            return self.state_handler.handle(devices, directive, header)

        # 3. Steuerbefehle (An/Aus, Dimmen, Rollladen, Heizung)
        return await self.control_handler.handle(devices, directive, header)
