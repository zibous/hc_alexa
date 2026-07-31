---
title: "🏠 Alexa Smart Home  – Geräte direkt steuern"
date: 2026-07-27T15:00:00
description: "Standalone Alexa Smart Home Skill der Shelly, Zigbee und Tasmota Geräte direkt per HTTP und MQTT steuert – ohne HomeAssistant, mit eigenem Dashboard."
type: "post"
draft: false
image: "posts/smarthome-alexa/alexadashboard.png"
author: "Peter Siebler"
snap_gallery: true
gallery: true
categories:
  - "Smarthome"
tags: ["docker", "python", "fastapi", "dashboard", "mqtt", "alexa", "zigbee", "shelly"]
---

[![GITHUB: HC_ALEXA](https://img.shields.io/badge/Project-GitHub-yellow.svg)](https://github.com/zibous/hc_alexa)
[![Support author](https://img.shields.io/badge/buy%20me%20a%20coffee-orange.svg)](https://www.buymeacoff.ee/zibous)
[![License](https://img.shields.io/badge/license-Open%20Source-green.svg)](https://opensource.org)
![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)

## Alexa direkt an die Hardware

Wer Smart-Home-Geräte über Alexa steuern will, braucht normalerweise HomeAssistant als Middleware. Das funktioniert, bringt aber einen schweren Container mit sich der regelmäßig Breaking Changes hat. **hc_alexa** macht es anders: Ein schlanker FastAPI-Service empfängt die Alexa-Directives von AWS Lambda und steuert die Geräte **direkt** per HTTP (Shelly) oder MQTT (Zigbee2MQTT, Tasmota).

<!--more-->

## Warum ohne HomeAssistant?

- **Ressourcen** – HA braucht 2+ GB RAM, hc_alexa braucht 50 MB
- **Stabilität** – Keine Breaking Changes bei HA-Updates
- **Geschwindigkeit** – Direkter HTTP-Call zum Shelly statt HA → Shelly Integration → HTTP
- **Transparenz** – Eine YAML-Datei definiert alle Geräte, ein Python-File pro Handler
- **Unabhängigkeit** – Eigener OAuth2-Endpoint, kein HA für Account Linking nötig
- **Dashboard** – Eigenes Web-UI mit Apple-Style Controls für Rollläden, Lichter, Thermostate

---

## 🏗️ Architektur

<p style="text-align:center;font-weight:600;font-size:1.8rem">☁️ Amazon Cloud</p>

{{< mermaid >}}
flowchart TD
    Echo[Alexa Echo] --> Service[Alexa Service]
    Service --> Skill[Smart Home Skill]
    Skill --> Lambda[AWS Lambda]
    Lambda -->|"HTTPS POST JSON HC ALEXA"| OUT((" "))
{{< /mermaid >}}

<p style="text-align:center;font-weight:600;font-size:1.8rem">🏠 Lokales Netzwerk</p>

{{< mermaid >}}
flowchart TD
    IN((" ")) -->|"HTTPS POST JSON HC ALEXA"| Nginx["Nginx SSL:443"]
    Nginx --> App["hc_alexa FastAPI :5018"]
    App --> Shelly["Shelly HTTP"]
    App --> Zigbee["Zigbee2MQTT"]
    App --> ESPHome["ESPHome HTTP"]
    App --> Tasmota["Tasmota MQTT"]
{{< /mermaid >}}

Der gesamte Flow: Alexa sendet einen JSON-Payload über AWS Lambda an den Server. Nginx terminiert SSL, FastAPI routet den Request an den passenden Handler (Discovery, Control, State). Der Handler steuert das Gerät direkt – ohne Umwege.

---

## 🔄 Alexa StateReport

Alexa fragt regelmäßig (ca. alle 60 Sekunden) den Status aller Geräte per `ReportState` ab. Die Antwort enthält je nach Gerätetyp die passenden Properties:

| Gerätetyp | Alexa Properties |
|-----------|-----------------|
| Temperatursensor | `TemperatureSensor.temperature` |
| Thermostat | `ThermostatController.targetSetpoint` + `thermostatMode` + `TemperatureSensor.temperature` |
| Schalter / Licht | `PowerController.powerState` |
| Rollladen | `RangeController.rangeValue` |

Wichtig für die korrekte Zuordnung:
- Antwort-Header muss `"name": "StateReport"` sein (nicht `"Response"`)
- Die `endpointId` muss exakt dem Format der Anfrage entsprechen (mit `#`-Trennzeichen)
- `EndpointHealth.connectivity` wird immer mitgesendet

---

## 🎮 Unterstützte Protokolle

| Protokoll | Zugriff | Geräte |
|-----------|---------|--------|
| **Shelly** | HTTP REST API | Rollläden, Schalter, Dimmer |
| **Zigbee2MQTT** | MQTT Publish/Subscribe | Temperatursensoren, Thermostate, RGB-Lichter |
| **ESPHome** | HTTP POST mit custom Endpoints | Türöffner, Spezial-Sensoren |
| **Tasmota** | MQTT (cmnd/stat Topics) | Sonoff Schalter, Multi-Kanal-Relais |

Alle Geräte werden in einer einzigen `devices.yaml` definiert:

```yaml
- id: cover.rollladen_kueche
  name: "Rollladen Küche"
  type: roller
  category: INTERIOR_BLIND
  protocol: shelly
  ip: "10.1.1.160"
  channel: "0"
  hardware: Shelly 2PM

- id: climate.thermostat_bad
  name: "Heizung Bad"
  type: thermostat
  category: THERMOSTAT
  protocol: z2m
  topic_id: thermostat-bad
  hardware: Tuya TS0601

- id: sensor.weather_kitchen_temperature
  name: "Temperatur Küche"
  type: sensor
  category: TEMPERATURE_SENSOR
  protocol: z2m
  topic_id: weather-kitchen
  hardware: Aqara Temperatursensor
```

---

## 📱 Dashboard

Statt der Alexa-App gibt es ein eigenes Web-Dashboard mit modernen Controls:

- **Rollläden** – SVG-Fenster-Visualisierung mit Drag-to-Position
- **Thermostate** – Soll/Ist-Temperatur mit Modus-Buttons (Aus/Heizen/Auto)
- **Lichter** – Apple-Style Bulb-Button mit Glow-Effekt und Brightness-Slider
- **Schalter** – Große Power-Buttons mit grünem Glow bei aktiv
- **Sensoren** – Ring-Gauge für Temperatur, Rollenzähler für m³-Werte

Das Frontend ist modular aufgebaut (10 JS-Module, 8 CSS-Dateien, alle < 80 Zeilen) und wird mit esbuild gebundelt.

### Dashboard
{{< gallery >}}
  {{< image-dir >}}
{{< /gallery >}}

---

## 🔐 OAuth2 Account Linking

hc_alexa hat einen eigenen OAuth2-Endpoint für das Alexa Account Linking. Damit ist **kein HomeAssistant** nötig um den Skill zu aktivieren oder neu zu verlinken:

- Authorization: `https://<domain>/oauth/authorize`
- Token: `https://<domain>/oauth/token`

Der OAuth-Flow gibt ein statisches Bearer-Token zurück. Für einen privaten Skill reicht das vollkommen aus.

---

## 🔌 AWS Lambda & Alexa Skill

Der AWS-Teil ist minimal – eine einzige Lambda-Funktion die den Request weiterleitet:

```python
import os, json, urllib3

def lambda_handler(event, context):
    base_url = os.environ.get('BASE_URL', '').strip("/")
    http = urllib3.PoolManager(
        cert_reqs='CERT_NONE',
        timeout=urllib3.Timeout(connect=2.0, read=10.0)
    )
    response = http.request(
        'POST',
        f'{base_url}/api/alexa/smart_home',
        headers={'Content-Type': 'application/json'},
        body=json.dumps(event).encode('utf-8'),
    )
    if response.status >= 400:
        return {'event': {'payload': {'type': 'INTERNAL_ERROR',
                'message': response.data.decode("utf-8")}}}
    return json.loads(response.data.decode('utf-8'))
```

Der Skill wird in der Alexa Developer Console als "Smart Home" Skill angelegt und mit der Lambda-Funktion verbunden.

---

## 📊 Status-Daten

Die Sensor-Werte kommen aus zwei Quellen:

1. **Initialer Load** – Z2M `state.json` wird beim Container-Start per SCP vom Zigbee-Server geholt
2. **Live-Updates** – MQTT Subscribe auf `conbee2mqtt/#` für Echtzeit-Änderungen
3. **Shelly/ESPHome** – HTTP-Status bei jedem Dashboard-Refresh parallel abgefragt

{{< mermaid >}}
flowchart LR
    Z2M["Z2M Server"] -->|"SCP state.json"| Cache["StatusCache"]
    EMQX["EMQX Broker"] -->|"MQTT conbee2mqtt/#"| Cache
    Cache --> Dashboard["Dashboard + Alexa API"]
    Dashboard -->|"HTTP GET /relay/0"| Shelly["Shelly / ESP"]
{{< /mermaid >}}

---

## 🛠️ Entwicklung & Deployment

```bash
make dev          # Lokaler Dev-Server (Hot-Reload)
make rebuild      # Docker neu bauen (inkl. Z2M-Sync)
make logs         # Docker Logs verfolgen
make test-*       # Alexa-Requests simulieren
make jsbuild      # Frontend bundeln
```

Der komplette Stack: Python 3.12, FastAPI, paho-mqtt, httpx – verpackt in einem 80MB Docker-Image.

---

## ⚠️ Hinweise

- **Proaktive ChangeReports** erfordern ein LWA (Login with Amazon) Refresh Token. Aktuell pollt Alexa per StateReport alle ~60s. Für Echtzeit-Push muss "Send Alexa Events" im Skill aktiviert werden.
- **Skill-Wechsel** führt zum Verlust aller Raum-Zuordnungen und Routinen. Geräte bleiben als "Geister" nach Skill-Deaktivierung.
- **Namenskonflikte** bei Sensor und Thermostat im gleichen Raum – Lösung: Eindeutige Namen oder Alexa-Raum-Zuordnung.

---

## 💡 Fazit

Nach der Umstellung von HomeAssistant auf hc_alexa:

- **RAM-Verbrauch**: 2.1 GB → 48 MB
- **Startzeit**: 45s → 2s
- **Reaktionszeit Alexa→Gerät**: ~800ms → ~200ms
- **Wartungsaufwand**: HA-Updates, Integrations-Probleme → eine YAML-Datei pflegen
- **Temperaturwerte**: Echtzeit-Synchronisation zwischen Dashboard und Alexa App

Für ein Smart Home mit Shelly, Zigbee und ein paar Tasmota-Geräten ist das völlig ausreichend. Wer keine Automationen, Szenen oder History-Graphen braucht, kann HomeAssistant getrost abschalten.

<hr style="margin-bottom: 4rem">

{{< notice tip >}}
Der komplette Source-Code ist auf GitHub verfügbar. Die Einrichtung dauert ca. 30 Minuten: devices.yaml anlegen, AWS Lambda erstellen, Skill aktivieren – fertig.
{{< /notice >}}
