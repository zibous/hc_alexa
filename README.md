# hc_alexa – Smart Home Alexa Controller

Standalone Smart Home Skill ohne HomeAssistant.  
Steuert Geräte direkt per HTTP (Shelly/ESPHome) und MQTT (Zigbee2MQTT/Tasmota).

## Architektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AMAZON CLOUD                                │
│                                                                     │
│   Alexa Echo ──→ Alexa Service ──→ Smart Home Skill ──→ AWS Lambda  │
│                                                                     │
└──────────────────────────────────────────┬──────────────────────────┘
                                           │ HTTPS POST (JSON)
                                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         LOKALES NETZWERK                            │
│                                                                     │
│   ┌──────────┐     ┌────────────────┐     ┌─────────────────────┐   │
│   │  Nginx   │────▶│  hc_alexa      │────▶│  Geräte             │   │
│   │  (SSL)   │     │  FastAPI :5018 │     │                     │   │
│   │  :443    │◀────│                │◀────│  Shelly (HTTP)      │   │
│   └──────────┘     │  Dashboard     │     │  Zigbee (MQTT/z2m)  │   │
│                    │  Alexa API     │     │  ESPHome (HTTP)     │   │
│                    │  KPI API       │     │  Tasmota (MQTT)     │   │
│                    └────────────────┘     └─────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Datenfluss Detail

```
ALEXA BEFEHL: "Alexa, Rollladen Küche auf 50%"

  ┌──────────┐    ┌─────────┐    ┌──────────┐    ┌────────────┐    ┌────────┐
  │  Alexa   │───▶│  AWS    │───▶│  Nginx   │───▶│  FastAPI   │───▶│ Shelly │
  │  Echo    │    │  Lambda │    │  :443    │    │  :5018     │    │ HTTP   │
  │          │◀───│         │◀───│          │◀───│            │◀───│        │
  └──────────┘    └─────────┘    └──────────┘    └────────────┘    └────────┘
       🗣️             ☁️              🔒              🐍              💡
   "Ok, erledigt"   Python       SSL Termination   Alexa Handler    Gerät

ALEXA FRAGE: "Alexa, wie warm ist es in der Küche?"

  Alexa ──▶ Lambda ──▶ Nginx ──▶ FastAPI ──▶ StatusCache (MQTT/Z2M)
    ◀── "25.3 Grad" ◀── JSON ◀── Response ◀── weather-kitchen: 25.3°C
```

## Protokolle

| Protokoll | Zugriff | Status-Abruf | Beispiel |
|-----------|---------|--------------|----------|
| `shelly` | HTTP GET `http://{ip}/relay/{ch}?turn=on` | HTTP GET Status | Rollläden, Schalter, Dimmer |
| `z2m` | MQTT `{Z2M_TOPIC_BASE}/{topic_id}/set` | Z2M state.json + MQTT Live | Sensoren, Thermostate |
| `esphome` | HTTP POST `http://{ip}/{endpoint_on}` | HTTP GET `http://{ip}/{endpoint_status}` | Türöffner |
| `mqtt` | MQTT Publish auf `topic` | MQTT Subscribe auf `topic_id` | Tasmota Schalter/Sensoren |

## Geräte-Konfiguration (devices.yaml)

```yaml
- id: rollladen_kueche          # Alexa Endpoint-ID
  name: "Rollladen Küche"       # Alexa friendly name
  type: roller                   # switch, dimmer, light, roller, thermostat, sensor
  category: INTERIOR_BLIND      # Alexa Display Category
  protocol: shelly              # shelly, z2m, esphome, mqtt
  ip: "10.1.1.160"             # Nur bei HTTP-Geräten
  channel: "0"                  # Nur bei Shelly
  topic_id: null               # MQTT Topic für Status (bei z2m: friendly_name)
  topic: null                  # MQTT Topic für Befehle (bei mqtt-Protokoll)
  value_path: null             # JSON-Pfad bei verschachtelter Payload
  unit: null                   # Einheit (°C, m³) – null = °C
  alexa: true                  # false = nur Dashboard, kein Alexa
  hardware: "Shelly 2PM"
```

## Projektstruktur

```
hc_alexa/
├── app/
│   ├── api/
│   │   ├── alexa_router.py        POST /api/alexa/smart_home
│   │   ├── dashboard_router.py    GET /api/devices, POST /api/control
│   │   └── kpi_router.py          GET /api/kpidata
│   ├── config/
│   │   ├── settings.py            Pydantic Settings aus .env
│   │   └── logging_config.py
│   ├── core/
│   │   └── device_loader.py       Lädt devices.yaml (cached)
│   ├── infrastructure/
│   │   ├── mqtt_client.py         Persistenter MQTT Publisher
│   │   └── status_cache.py        Z2M State + MQTT Live-Updates
│   ├── models/
│   │   └── device.py              DeviceConfig Pydantic Model
│   ├── processor/
│   │   ├── alexa_processor.py     Routing: Discovery/Control/State
│   │   ├── handlers/
│   │   │   ├── discovery.py       Alexa.Discovery Handler
│   │   │   ├── control.py         Power/Brightness/Position/Thermostat
│   │   │   └── state.py           ReportState (Temperatur)
│   │   └── helpers.py
│   ├── schemas/
│   │   └── kpi.py
│   ├── services/
│   │   ├── kpi_service.py
│   │   └── access_log.py
│   └── main.py
├── data/
│   ├── devices.yaml               Geräte-Konfiguration
│   ├── z2m_state.json             Z2M State (via sync_z2m.sh)
│   └── z2m_config.yaml            Z2M Config (via sync_z2m.sh)
├── frontend/static/
│   ├── index.html
│   ├── css/                        Modulares CSS (8 Dateien)
│   └── js/                         Modulares JS (10 Dateien)
├── scripts/
│   └── sync_z2m.sh               Z2M-Daten per SCP holen
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
└── .env
```

## Makefile Befehle

```bash
make dev              # Lokaler Dev-Server mit Auto-Reload
make sync-z2m         # Z2M State-Dateien vom Remote holen
make up               # Docker starten (mit Z2M-Sync)
make rebuild          # Docker neu bauen + starten
make jsbuild          # Frontend JS/CSS bundeln
make test-discovery   # Alexa Discovery simulieren
make test-power-on    # Schalter einschalten testen
make test-roller      # Rollladen Position testen
make test-thermostat  # Thermostat setzen testen
make test-sensor      # Temperatur abfragen testen
make test-dashboard   # Dashboard API testen
make test-health      # Health-Check
```

---

## AWS Lambda einrichten

### 1. Lambda-Funktion erstellen

AWS Console → Lambda → Funktion erstellen:
- Name: `alexa-smart-home-skill`
- Runtime: Python 3.12
- Architektur: arm64 (günstiger)

### 2. Lambda-Code

```python
"""AWS Lambda Handler für Alexa Smart Home Skill."""
import json
import urllib.request

# Dein Server (HTTPS, via Nginx)
ENDPOINT = "https://ips.siebler.at/api/alexa/smart_home"

def lambda_handler(event, context):
    """Leitet den Alexa-Request an deinen Server weiter."""
    payload = json.dumps(event).encode("utf-8")

    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {
            "event": {
                "header": {
                    "namespace": "Alexa",
                    "name": "ErrorResponse",
                    "payloadVersion": "3",
                    "messageId": event.get("directive", {}).get("header", {}).get("messageId", ""),
                },
                "payload": {
                    "type": "BRIDGE_UNREACHABLE",
                    "message": str(e),
                },
            }
        }
```

### 3. Lambda-Konfiguration
- Timeout: **10 Sekunden** (Alexa erlaubt max 8s)
- Memory: **128 MB** (reicht für URL-Forward)
- Trigger: Wird vom Alexa Skill hinzugefügt (Schritt 5)

---

## Alexa Smart Home Skill erstellen

### 4. Skill in der Alexa Developer Console

1. Öffne https://developer.amazon.com/alexa/console/ask
2. **Create Skill**
   - Name: `Mein Smart Home`
   - Locale: `German (DE)`
   - Type: **Smart Home**
   - Hosting: **Provision your own** (nicht Alexa-hosted)
3. **Smart Home Service Endpoint**
   - Default endpoint: ARN deiner Lambda-Funktion
   - (z.B. `arn:aws:lambda:eu-west-1:123456789:function:alexa-smart-home-skill`)

### 5. Lambda Trigger konfigurieren

AWS Console → Lambda → deine Funktion → Trigger hinzufügen:
- Trigger: **Alexa Smart Home**
- Skill ID: Die Skill-ID aus der Developer Console (Format: `amzn1.ask.skill.xxx-xxx-xxx`)

### 6. Account Linking (optional aber empfohlen)

Für einen privaten Skill ohne Account Linking:
- In der Developer Console → Permissions → keine aktivieren
- Der Skill funktioniert ohne OAuth (da er nur auf deinem Account läuft)

Alternativ: Setze ein einfaches Bearer-Token in den Authorization-Header das dein Nginx prüft.

---

## Alexa App: Skill aktivieren

### 7. Skill in der Alexa App aktivieren

1. Öffne die **Alexa App** auf dem Handy
2. **Mehr → Skills & Spiele → Deine Skills → Entwickler**
3. Dein Skill `Mein Smart Home` erscheint dort
4. **Aktivieren**
5. Alexa führt automatisch eine **Discovery** durch
6. Alle Geräte aus `devices.yaml` erscheinen in der Alexa App

### 8. Geräte testen

```
"Alexa, suche nach neuen Geräten"
"Alexa, Rollladen Küche auf 50 Prozent"
"Alexa, schalte Gartenbrunnen ein"
"Alexa, wie warm ist es in der Küche?"
"Alexa, stelle Heizung Bad auf 22 Grad"
"Alexa, schalte Heizung Bad auf Heizen"
```

---

## Nginx-Konfiguration

```nginx
# Alexa Smart Home Endpoint (AWS Lambda → FastAPI)
set $alexa_backend "http://localhost:5018";

location /api/alexa/smart_home {
    proxy_pass $alexa_backend$request_uri;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header Authorization $http_authorization;
}

# Dashboard (Browser)
location ^~ /dashboardalexa/ {
    proxy_pass http://10.1.1.119:5018/;
}
```

---

## Umgebungsvariablen (.env)

```env
MQTT_HOST=10.1.1.198
MQTT_PORT=4883
MQTT_USER=smarthome
MQTT_PASS=********
MQTT_KEEPALIVE=60
Z2M_TOPIC_BASE=conbee2mqtt
DEVICES_YAML_PATH=data/devices.yaml
```

---

## Status-Daten Synchronisation

```
┌──────────────┐    SCP beim Start      ┌──────────────┐
│  NUC2020     │ ──────────────────────▶│  hc_alexa    │
│  Z2M Server  │    state.json          │  data/       │
│              │    configuration.yaml  │              │
└──────────────┘                        └──────┬───────┘
                                               │
                    MQTT Live-Updates          │ Liest beim Start
                    (conbee2mqtt/#)            ▼
┌──────────────┐                        ┌──────────────┐
│  EMQX        │ ──────────────────────▶│  StatusCache │
│  Broker      │    Thermostat/Sensor   │  (Memory)    │
│  :4883       │    Änderungen          │              │
└──────────────┘                        └──────────────┘
```
