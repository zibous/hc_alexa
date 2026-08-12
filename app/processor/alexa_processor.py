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

        # Endpoint-ID: Original merken, dann normalisieren für Device-Lookup
        endpoint = directive.get("endpoint", {})
        original_endpoint_id = endpoint.get("endpointId", "")
        if "endpointId" in endpoint:
            # switch#panasonic_mikrowelle → switch.panasonic_mikrowelle (für Lookup)
            endpoint["endpointId"] = endpoint["endpointId"].replace("#", ".")

        devices = load_devices()

        # 1. Geräte-Erkennung
        if namespace == "Alexa.Discovery":
            return self.discovery_handler.handle(devices, header)

        # 2. Statusabfragen (z.B. Temperatursensor)
        if namespace == "Alexa" and header.get("name") == "ReportState":
            response = await self.state_handler.handle(devices, directive, header)
            # endpointId in Original-Format (mit #) zurückgeben
            response["event"]["endpoint"]["endpointId"] = original_endpoint_id
            return response

        # 3. Steuerbefehle (An/Aus, Dimmen, Rollladen, Heizung)
        result = await self.control_handler.handle(devices, directive, header)
        # Auch bei Control-Responses die Original-ID verwenden
        if "event" in result and "endpoint" in result["event"]:
            result["event"]["endpoint"]["endpointId"] = original_endpoint_id
        return result
