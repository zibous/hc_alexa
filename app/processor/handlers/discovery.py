# app/processor/handlers/discovery.py – Alexa Discovery (HA-kompatibles Format)
from typing import List
from app.models.device import DeviceConfig


class DiscoveryHandler:
    def handle(self, devices: List[DeviceConfig], header: dict) -> dict:
        endpoints = []
        for d in devices:
            if not d.alexa:
                continue
            endpoint = self._build_endpoint(d)
            if endpoint:
                endpoints.append(endpoint)

        return {
            "event": {
                "header": {
                    "namespace": "Alexa.Discovery",
                    "name": "Discover.Response",
                    "payloadVersion": "3",
                    "messageId": header.get("messageId"),
                },
                "payload": {"endpoints": endpoints},
            }
        }

    def _build_endpoint(self, d: DeviceConfig) -> dict:
        capabilities = self._build_capabilities(d)
        endpoint_id = d.id.replace(".", "#")

        return {
            "displayCategories": [d.category],
            "cookie": {},
            "endpointId": endpoint_id,
            "friendlyName": d.name,
            "description": f"{d.hardware} via SmartHome Controller",
            "manufacturerName": "SmartHome",
            "additionalAttributes": {
                "manufacturer": "SmartHome",
                "model": d.type,
                "softwareVersion": "1.0.0",
                "customIdentifier": f"-{d.id}",
            },
            "capabilities": capabilities,
        }

    def _build_capabilities(self, d: DeviceConfig) -> list:
        caps = []

        if d.type == "switch":
            caps.append(self._power_controller())
            caps.append(self._contact_sensor())

        elif d.type in ("dimmer", "light"):
            caps.append(self._power_controller())
            caps.append(self._brightness_controller())

        elif d.type == "roller":
            caps.append(self._power_controller())
            caps.append(self._range_controller_cover())

        elif d.type == "thermostat":
            caps.append(self._power_controller())
            caps.append(self._thermostat_controller())
            caps.append(self._temperature_sensor())

        elif d.type == "sensor":
            caps.append(self._temperature_sensor())

        # EndpointHealth + Alexa Base (immer am Ende)
        caps.append(self._endpoint_health())
        caps.append({"type": "AlexaInterface", "interface": "Alexa", "version": "3"})

        return caps

    # ─── Capability Builders ─────────────────────────────

    def _power_controller(self) -> dict:
        return {
            "type": "AlexaInterface",
            "interface": "Alexa.PowerController",
            "version": "3",
            "properties": {
                "supported": [{"name": "powerState"}],
                "proactivelyReported": False,
                "retrievable": True,
            },
        }

    def _brightness_controller(self) -> dict:
        return {
            "type": "AlexaInterface",
            "interface": "Alexa.BrightnessController",
            "version": "3",
            "properties": {
                "supported": [{"name": "brightness"}],
                "proactivelyReported": False,
                "retrievable": True,
            },
        }

    def _contact_sensor(self) -> dict:
        return {
            "type": "AlexaInterface",
            "interface": "Alexa.ContactSensor",
            "version": "3",
            "properties": {
                "supported": [{"name": "detectionState"}],
                "proactivelyReported": False,
                "retrievable": True,
            },
        }

    def _temperature_sensor(self) -> dict:
        return {
            "type": "AlexaInterface",
            "interface": "Alexa.TemperatureSensor",
            "version": "3",
            "properties": {
                "supported": [{"name": "temperature"}],
                "proactivelyReported": False,
                "retrievable": True,
            },
        }

    def _thermostat_controller(self) -> dict:
        return {
            "type": "AlexaInterface",
            "interface": "Alexa.ThermostatController",
            "version": "3",
            "properties": {
                "supported": [{"name": "thermostatMode"}, {"name": "targetSetpoint"}],
                "proactivelyReported": False,
                "retrievable": True,
            },
            "configuration": {
                "supportsScheduling": False,
                "supportedModes": ["OFF", "HEAT", "AUTO"],
            },
        }

    def _range_controller_cover(self) -> dict:
        return {
            "type": "AlexaInterface",
            "interface": "Alexa.RangeController",
            "version": "3",
            "instance": "cover.position",
            "properties": {
                "supported": [{"name": "rangeValue"}],
                "proactivelyReported": True,
                "retrievable": True,
                "nonControllable": False,
            },
            "capabilityResources": {
                "friendlyNames": [
                    {"@type": "text", "value": {"text": "Position", "locale": "en-US"}},
                    {"@type": "asset", "value": {"assetId": "Alexa.Setting.Opening"}},
                ]
            },
            "configuration": {
                "supportedRange": {"minimumValue": 0, "maximumValue": 100, "precision": 1},
                "unitOfMeasure": "Alexa.Unit.Percent",
            },
            "semantics": {
                "actionMappings": [
                    {
                        "@type": "ActionsToDirective",
                        "actions": ["Alexa.Actions.Lower", "Alexa.Actions.Close"],
                        "directive": {"name": "SetRangeValue", "payload": {"rangeValue": 0}},
                    },
                    {
                        "@type": "ActionsToDirective",
                        "actions": ["Alexa.Actions.Raise", "Alexa.Actions.Open"],
                        "directive": {"name": "SetRangeValue", "payload": {"rangeValue": 100}},
                    },
                ],
                "stateMappings": [
                    {"@type": "StatesToValue", "states": ["Alexa.States.Closed"], "value": 0},
                    {
                        "@type": "StatesToRange",
                        "states": ["Alexa.States.Open"],
                        "range": {"minimumValue": 1, "maximumValue": 100},
                    },
                ],
            },
        }

    def _endpoint_health(self) -> dict:
        return {
            "type": "AlexaInterface",
            "interface": "Alexa.EndpointHealth",
            "version": "3",
            "properties": {
                "supported": [{"name": "connectivity"}],
                "proactivelyReported": False,
                "retrievable": True,
            },
        }
