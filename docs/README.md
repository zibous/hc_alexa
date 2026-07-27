# Spezifikation: FastAPI Alexa Docker-Anwendung (HA-free)

## 1. Architektur & Datenfluss

```bash
.
├── app
│   ├── api
│   │   └── alexa_router.py
│   ├── config
│   │   ├── logging_config.py
│   │   └── settings.py
│   ├── core
│   │   └── device_loader.py
│   ├── infrastructure
│   │   ├── mqtt_client.py
│   │   └── shelly_client.py
│   ├── __init__.py
│   ├── main.py
│   ├── models
│   │   └── device.py
│   ├── processor
│   │   ├── alexa_processor.py
│   │   ├── handlers
│   │   │   ├── control.py
│   │   │   ├── discovery.py
│   │   │   └── state.py
│   │   └── helpers.py
│   ├── schemas
│   └── service
├── data
│   └── devices.yaml
├── docs
│   ├── nginx_alexa.conf
│   └── README.md
├── frontend
├── logs
├── Makefile
├── pyrightconfig.json
└── test
```


1. HINWEG: Alexa-Zentrale ──> AWS Lambda ──> HTTPS (Port 443) ──> Nginx
2. VERARBEITUNG: Nginx ──> FastAPI (Port 8000) [Liest devices.yaml]
3. AKTION: FastAPI schaltet Hardware direkt:
   * Shelly (WLAN): Via HTTP-REST-API
   * Zigbee (z2m): Via MQTT-Publish
4. RÜCKWEG: FastAPI ──> Nginx ──> AWS Lambda ──> Alexa ──> 🗣️ "Ok!"

## 2. Geräte-Mapping (devices.yaml -> Alexa API)
* rollladen_kueche (Shelly HTTP) ──> Alexa.RangeController (Position)
* weather_outnorth... (Zigbee MQTT) ──> Alexa.TemperatureSensor
* thermostat_bad (Zigbee MQTT) ──> Alexa.ThermostatController
* lichtdimmer_kueche (Shelly HTTP) ──> Alexa.Power- & BrightnessController
* wasserbrunnen (Shelly HTTP) ──> Alexa.PowerController


## 3. Docker-Infrastruktur
* Container 1 (Nginx/SWAG): Übernimmt die SSL-Terminierung (Zwingend für AWS Lambda).
* Container 2 (FastAPI): Führt Python 3.11-slim aus. Installiert: `fastapi`, `uvicorn`, `pyyaml`, `httpx`, `paho-mqtt`.

## 4. Entwicklungs-Roadmap (To-Do)
* [ ] YAML-Parser: Skript schreiben, das beim Start `devices.yaml` einliest.
* [ ] Endpoint POST `/alexa`: Zentraler Einstiegspunkt für AWS Lambda Payloads.
* [ ] Alexa.Discovery: Handler für die automatische Gerätesuche in Alexa.
* [ ] Protokoll-Treiber: HTTP-Client (Shelly) und MQTT-Client (Zigbee) implementieren.
* [ ] Docker-Setup: `Dockerfile` und `docker-compose.yml` erstellen.
