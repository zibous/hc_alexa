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
- **Dashboard** – Eigenes Web-UI mit Apple-Style Controls für Rollläden, Lichter, Thermostate

---

## 🏗️ Architektur

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         AMAZON CLOUD                                │
│   Alexa Echo ──→ Alexa Service ──→ Smart Home Skill ──→ AWS Lambda  │
└──────────────────────────────────────────┬──────────────────────────┘
                                           │ HTTPS POST (JSON)
                                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         LOKALES NETZWERK                            │
│   ┌──────────┐     ┌────────────────┐     ┌─────────────────────┐   │
│   │  Nginx   │────▶│  hc_alexa      │────▶│  Geräte             │   │
│   │  SSL:443 │     │  FastAPI :5018 │     │  Shelly (HTTP)      │   │
│   │          │◀────│  Dashboard     │     │  Zigbee (MQTT/z2m)  │   │
│   └──────────┘     │  Alexa API     │     │  ESPHome (HTTP)     │   │
│                    │  KPI API       │     │  Tasmota (MQTT)     │   │
│                    └────────────────┘     └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

Der gesamte Flow: Alexa sendet einen JSON-Payload über AWS Lambda an meinen Server. Nginx terminiert SSL, FastAPI routet den Request an den passenden Handler (Discovery, Control, State). Der Handler steuert das Gerät direkt – ohne Umwege.

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
- id: rollladen_kueche
  name: "Rollladen Küche"
  type: roller
  category: INTERIOR_BLIND
  protocol: shelly
  ip: "10.1.1.160"
  channel: "0"

- id: thermostat_bad
  name: "Heizung Bad"
  type: thermostat
  category: THERMOSTAT
  protocol: z2m
  topic_id: thermostat-bad
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

## 🔌 AWS Lambda & Alexa Skill

Der AWS-Teil ist minimal – eine einzige Lambda-Funktion die den Request weiterleitet:

```python
import json, urllib.request

ENDPOINT = "https://<domain>/api/alexa/smart_home"

def lambda_handler(event, context):
    payload = json.dumps(event).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.loads(resp.read().decode("utf-8"))
```

Der Skill wird in der Alexa Developer Console als "Smart Home" Skill angelegt und mit der Lambda-Funktion verbunden. Keine OAuth-Konfiguration nötig für den privaten Gebrauch.

---

## 📊 Status-Daten

Die Sensor-Werte kommen aus zwei Quellen:

1. **Initialer Load** – Z2M `state.json` wird beim Container-Start per SCP vom Zigbee-Server geholt
2. **Live-Updates** – MQTT Subscribe auf `conbee2mqtt/#` für Echtzeit-Änderungen
3. **Shelly/ESPHome** – HTTP-Status bei jedem Dashboard-Refresh parallel abgefragt

```text
┌──────────────┐    SCP beim Start      ┌──────────────┐
│  Z2M Server  │ ──────────────────────▶│  StatusCache │
└──────────────┘    state.json          └──────┬───────┘
                                               │
┌──────────────┐    MQTT Live                  │
│  EMQX        │ ──────────────────────▶       │
│  Broker      │    conbee2mqtt/#              │
└──────────────┘                               ▼
                                      ┌──────────────┐
┌──────────────┐    HTTP GET          │  Dashboard   │
│  Shelly/ESP  │ ◀─────────────────── │  API         │
└──────────────┘    /relay/0          └──────────────┘
```

---

## 🛠️ Entwicklung & Deployment

```bash
make dev          # Lokaler Dev-Server (Hot-Reload)
make rebuild      # Docker neu bauen (inkl. Z2M-Sync)
make test-*       # Alexa-Requests simulieren
make jsbuild      # Frontend bundeln
```

Der komplette Stack: Python 3.12, FastAPI, paho-mqtt, httpx – verpackt in einem 80MB Docker-Image.

---

## 💡 Fazit

Nach der Umstellung von HomeAssistant auf hc_alexa:

- **RAM-Verbrauch**: 2.1 GB → 48 MB
- **Startzeit**: 45s → 2s
- **Reaktionszeit Alexa→Gerät**: ~800ms → ~200ms
- **Wartungsaufwand**: HA-Updates, Integrations-Probleme → eine YAML-Datei pflegen

Für ein Smart Home mit Shelly, Zigbee und ein paar Tasmota-Geräten ist das völlig ausreichend. Wer keine Automationen, Szenen oder History-Graphen braucht, kann HomeAssistant getrost abschalten.

<hr style="margin-bottom: 4rem">

{{< notice tip >}}
Der komplette Source-Code ist auf GitHub verfügbar. Die Einrichtung dauert ca. 30 Minuten: devices.yaml anlegen, AWS Lambda erstellen, Skill aktivieren – fertig.
{{< /notice >}}
