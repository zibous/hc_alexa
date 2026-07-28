# Dokumentation: Manuelle Alexa & Home Assistant Integration (Selbstbau-Skill)

Diese Anleitung beschreibt die manuelle (kostenlose) Verknüpfung von Home Assistant mit Amazon Alexa über die Amazon Developer Console und AWS Lambda.


```bash
1. DIE BESTELLUNG (Hinweg)
   [ Sie ] 🗣️ "Licht an!" ──> [ Alexa-Lautsprecher ] ──> [ Amazon Server ]
                                                            │
                                                            ▼
                                                     [ AWS Lambda ] (Der digitale Postbote)
                                                            │
                                                            ▼
                                                     [ Ihr Nginx ] (Das Werkstor)


2. DIE ZUSTELLUNG & AKTION (Bei Ihnen zu Hause)
   [ Ihr Nginx ] ──> [ Home Assistant ] ──> 💡 (Das Licht geht physikalisch an!)


3. DIE QUITTUNG (Rückweg)
   [ Home Assistant ] ──> [ Ihr Nginx ] ──> [ AWS Lambda ] ──> [ Amazon Server ]


4. DIE BESTÄTIGUNG (Antwort)
   [ Amazon Server ] ──> [ Alexa-Lautsprecher ] ──> 🗣️ "Ok!" ──> [ Zu Ihnen ]

```

Der Daten-Rückweg (Bestätigung)Wenn Home Assistant das Gerät geschaltet hat, wandert die Antwort im Bruchteil einer Sekunde rückwärts durch die Kette:


```bash
Home Assistant ➡️ Nginx ➡️ AWS Lambda ➡️ Alexa Cloud ➡️ Echo-Gerät 🗣️ (Antwortet: "Ok").
```


## Ablauf

```
Zusammenfassend: Wer spricht mit wem?

Amazon startet ➡️ Lambda-Python-Skript.
Lambda-Skript startet ➡️ Nginx-Routing-Skript.
Nginx startet ➡️ Home-Assistant-Alexa-Skript.

```

---

## 📋 Voraussetzungen

1. **Öffentliche HTTPS-URL:** Home Assistant muss extern über HTTPS erreichbar sein (z. B. via DuckDNS + Nginx).
2. **Nginx-Konfiguration:** Die`location`-Blöcke müssen in Nginx aktiv und fehlerfrei geladen sein.
3. **Accounts:**
   * Amazon Developer Account (kostenlos) -> [://amazon.com](https://developer.amazon.com/alexa/console/ask)
   * AWS Web Services Account (kostenlos / Free Tier) -> [://amazon.com](https://aws.amazon.com)


---


## 🛠️ Nginx-Konfiguration

```bash
    # =============================================================================
    # locations/alexa.conf — Alexa Skills (Flash Briefings + Smart Home)
    # Reine REST-Calls von Amazon, kein WebSocket nötig
    # set $host_homeassitant localhost:8123;
    # =============================================================================


    # ----  Homeassitant Alexa briefings  -----
    location /api/alexa/flash_briefings/ {
        allow all;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect http:// https://;
        proxy_pass http://localhost:8123$request_uri;
    }
    # ----  Homeassitant Alexa Smarthome skill -----
    location /api/alexa/smart_home {
        allow all;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Authorization $http_authorization;
        proxy_redirect http:// https://;
        proxy_pass http://localhost:8123$request_uri;
    }
```

## 🛠️ Schritt 1: Home Assistant Vorbereitung

Fügen Sie Ihrer `configuration.yaml` in Home Assistant folgende Konfiguration hinzu, um die Alexa-Schnittstelle zu aktivieren.

```yaml
# configuration.yaml
alexa:
  smart_home:
    # Optional: Bestimmte Entitäten ein- oder ausschließen
    filter:
      include_entities:
        - light.wohnzimmer
        - switch.kaffeemaschine
      exclude_domains:
        - automation
```

*Danach Home Assistant neu starten (`Entwicklerwerkzeuge` -> `YAML` -> `Neu starten`).*

---

## ☁️ Schritt 2: AWS Lambda Funktion erstellen

Da Alexa Smart Home Skills direkt mit AWS Lambda kommunizieren, wird eine "Brücke" benötigt, die Anfragen an Ihren Nginx-Server weiterleitet.

1. Loggen Sie sich in die **AWS Management Console** ein.
2. Ändern Sie die Region oben rechts zwingend auf **EU (Irland) / eu-west-1** (wichtig für europäische Alexa-Geräte).
3. Suchen Sie nach dem Dienst **Lambda** und klicken Sie auf **Funktion erstellen**.
4. Wählen Sie **Von Grund auf neu erstellen**:
   * **Funktionsname:** `HomeAssistantAlexaSkill`
   * **Laufzeit:** `Python 3.10` (oder höher)
   * **Architektur:** `x86_64`
5. Klicken Sie auf **Funktion erstellen**.

### Code einfügen
Ersetzen Sie den Code im Datei-Editor (`lambda_function.py`) durch folgendes Python-Skript. Passen Sie die URL in Zeile 6 an!

```python
import json
import urllib.request

def lambda_handler(event, context):

    # ÄNDERN SIE DIESE URL ZU IHRER HOME ASSISTANT ADRESSE:
    base_url = "https://IHRE-DYNDNS-ODER-DOMAIN.de"

    # Bestimmung des Endpunkts basierend auf dem Event-Typ
    if event.get('directive', {}).get('header', {}).get('namespace') == 'Alexa.Discovery':
        url = f"{base_url}/api/alexa/smart_home"
    else:
        url = f"{base_url}/api/alexa/smart_home"

    headers = {
        'Content-Type': 'application/json',
    }

    # Weiterleitung des Alexa-Requests an Nginx/Home Assistant
    req = urllib.request.Request(url, data=json.dumps(event).encode('utf-8'), headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Fehler bei der Verbindung zu Home Assistant: {e}")
        return {}
```

6. Klicken Sie auf **Deploy** (Bereitstellen).
7. Kopieren Sie die **ARN** (oben rechts, z. B. `arn:aws:lambda:eu-west-1:123456789012:function:HomeAssistantAlexaSkill`).

---

## 👩‍💻 Schritt 3: Amazon Developer Console (Skill anlegen)

1. Öffnen Sie die [Alexa Developer Console](https://://amazon.com/alexa/console/alexa-skills-kit).
2. Klicken Sie auf **Create Skill**:
   * **Skill Name:** `Home Assistant Smart Home`
   * **Primary Language:** `German`
   * **Choose a model:** `Smart Home` (Sehr wichtig!)
   * **Hosting-Methode:** `Provision your own`
3. Klicken Sie oben rechts auf **Next**.
4. Wählen Sie im nächsten Fenster **Smart Home** aus und klicken Sie auf **Create Skill**.

### Smart Home Service Endpoint konfigurieren
1. Suchen Sie im linken Menü nach **Endpoint**.
2. Wählen Sie **AWS Lambda ARN** als Service-Endpoint-Typ.
3. Fügen Sie unter **Default Region** die kopierte ARN aus Schritt 2 ein.
4. Kopieren Sie Ihre **Your Skill ID** (wird auf dieser Seite angezeigt, z. B. `amzn1.echo-sdk-ams.app...`). **Noch nicht speichern!**

---

## 🔏 Schritt 4: AWS Lambda mit Alexa verknüpfen

Gehen Sie zurück zu Ihrem Tab mit der **AWS Lambda Funktion**:

1. Klicken Sie im Bereich "Funktionsübersicht" auf **+ Auslöser hinzufügen**.
2. Wählen Sie **Alexa Skills Kit** aus der Liste.
3. Fügen Sie bei **Skill-ID-Verifizierung** die soeben kopierte **Your Skill ID** aus der Developer Console ein.
4. Klicken Sie auf **Hinzufügen**.
5. Gehen Sie zurück zur **Alexa Developer Console** und klicken Sie nun dort auf **Save** (Speichern) im Endpoint-Fenster.

---

## 🔑 Schritt 5: Account Linking (Konto-Verknüpfung)

Damit Alexa sich bei Home Assistant anmelden darf, muss OAuth2 eingerichtet werden.

1. In der Alexa Developer Console links auf **Account Linking** klicken.
2. Füllen Sie die Felder exakt wie folgt aus (Ersetzen Sie `https://IHRE-DOMAIN.de` mit Ihrer echten URL):

| Feld | Wert |
| :--- | :--- |
| **Security Profile** | *Wird automatisch generiert* |
| **Authorization URI** | `https://ihre-domain.de` |
| **Access Token URI** | `https://ihre-domain.de` |
| **Client ID** | `https://amazon.com` (Für Europa/Deutschland) |
| **Client Secret** | *Ein beliebiges Passwort eingeben (wird von HA ignoriert, ist aber Pflichtfeld)* |
| **Client Authentication Scheme** | `Credentials in request body` |
| **Scope** | Klicken Sie auf *Add scope* und geben Sie `smart_home` ein. |

3. Scrollen Sie ganz nach unten. Dort finden Sie **Alexa Redirect URLs** (z. B. `https://amazon.comapi/skill/link/XXXXXX`).
4. **Wichtig für Home Assistant:** Kopieren Sie diese Redirect-URL. Sie müssen diese URL in Home Assistant nicht zwingend eintragen, Home Assistant akzeptiert die Anfrage der Amazon-Server automatisch, solange die Client-ID stimmt.
5. Klicken Sie oben rechts auf **Save**.

---

## 📱 Schritt 6: Aktivierung & Kontrolle

### 1. Skill aktivieren
1. Öffnen Sie die **Alexa App** auf Ihrem Smartphone oder gehen Sie auf [alexa.amazon.de](https://amazon.de).
2. Navigieren Sie zu **Mehr** -> **Skills und Spiele** -> **Ihre Skills** -> **Entwickler**.
3. Dort sehen Sie Ihren Skill `Home Assistant Smart Home`.
4. Klicken Sie auf **Zur Verwendung aktivieren**.
5. Ein Browserfenster öffnet sich. Loggen Sie sich mit Ihren **Home Assistant Benutzerdaten** ein und bestätigen Sie den Zugriff.

### 2. Gerätesuche (Kontrolle)
* Nach erfolgreichem Login startet Alexa automatisch die Gerätesuche.
* Alternativ sagen Sie: *"Alexa, suche nach neuen Geräten."*
* Wenn alles klappt, tauchen Ihre in `configuration.yaml` definierten Geräte in der Alexa-App auf.

---

## 🔍 Fehlerbehebung & Protokolle (Logs)

Sollte etwas nicht funktionieren, prüfen Sie die Kette von außen nach innen:

1. **Nginx prüfen:** Steht im Nginx Error-Log (`/var/log/nginx/error.log`), dass Anfragen blockiert werden? (Sicherstellen, dass `allow all;` aktiv ist).
2. **AWS Lambda testen:** Öffnen Sie Ihre Lambda-Funktion in AWS, gehen Sie auf den Reiter **Test**, erstellen Sie ein leeres Test-Event und führen Sie es aus. Wenn dort ein Time-Out oder Verbindungsfehler steht, erreicht AWS Ihren Nginx-Server nicht (z.B. wegen einer Firewall oder falscher URL).
3. **Home Assistant Logs:** Unter *Einstellungen -> System -> Protokolle* nach Einträgen bezüglich `alexa` suchen.
