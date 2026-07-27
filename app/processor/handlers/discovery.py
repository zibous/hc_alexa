from typing import List
from app.models.device import DeviceConfig

class DiscoveryHandler:
    def handle(self, devices: List[DeviceConfig], header: dict) -> dict:
        endpoints = []
        for d in devices:
            if not d.alexa:
                continue
            capabilities = [{"type": "AlexaInterface", "interface": "Alexa", "version": "3"}]
            
            if d.type in ["switch", "dimmer", "light"]:
                capabilities.append({"type": "AlexaInterface", "interface": "Alexa.PowerController", "version": "3", "properties": {"supported": [{"name": "powerState"}], "retrievable": True, "proactivelyReported": False}})
            if d.type in ["dimmer", "light"]:
                capabilities.append({"type": "AlexaInterface", "interface": "Alexa.BrightnessController", "version": "3", "properties": {"supported": [{"name": "brightness"}], "retrievable": True, "proactivelyReported": False}})
            if d.type == "roller":
                capabilities.append({"type": "AlexaInterface", "interface": "Alexa.RangeController", "version": "3", "instance": "Blind.Position", "properties": {"supported": [{"name": "rangeValue"}], "retrievable": True, "proactivelyReported": False}, "configuration": {"supportedRange": {"minimumValue": 0, "maximumValue": 100, "precision": 1}, "unitOfMeasure": "Alexa.Unit.Percent"}})
            if d.type == "thermostat":
                capabilities.append({"type": "AlexaInterface", "interface": "Alexa.ThermostatController", "version": "3", "properties": {"supported": [{"name": "targetSetpoint"}, {"name": "thermostatMode"}], "retrievable": True, "proactivelyReported": False}, "configuration": {"supportedModes": ["HEAT", "AUTO", "OFF"]}})
            if d.type == "sensor":
                capabilities.append({"type": "AlexaInterface", "interface": "Alexa.TemperatureSensor", "version": "3", "properties": {"supported": [{"name": "temperature"}], "retrievable": True, "proactivelyReported": False}})

            endpoints.append({
                "endpointId": d.id,
                "manufacturerName": d.protocol.upper(),
                "friendlyName": d.name,
                "description": f"{d.hardware} via SmartHome Controller",
                "displayCategories": [d.category],
                "capabilities": capabilities
            })
            
        return {
            "event": {
                "header": {"namespace": "Alexa.Discovery", "name": "Discover.Response", "payloadVersion": "3", "messageId": header.get("messageId")},
                "payload": {"endpoints": endpoints}
            }
        }
