# AWS Lambda + Alexa Skill – Setup & Prüfung

## Übersicht der Komponenten

```
┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────┐
│  Alexa Developer     │     │  AWS Lambda          │     │  Dein Server │
│  Console             │     │  Console             │     │              │
│                      │     │                      │     │              │
│  Skill               │────▶│  Funktion            │────▶│  Nginx:443   │
│  (Smart Home Type)   │     │  (Python Forward)    │     │  → :5018     │
│                      │     │                      │     │              │
│  Skill ID:           │     │  ARN:                │     │  Endpoint:   │
│  amzn1.ask.skill.xxx │     │  arn:aws:lambda:...  │     │  /api/alexa/ │
└──────────────────────┘     └──────────────────────┘     └──────────────┘
```

---

## 1. AWS Lambda prüfen

### Wo finden?
https://console.aws.amazon.com/lambda → Region prüfen (vermutlich `eu-west-1` Ireland)

### Was prüfen?
- **Funktionsname**: z.B. `alexa-smart-home` oder ähnlich
- **Runtime**: Python 3.x
- **Trigger**: Muss "Alexa Smart Home" zeigen mit deiner Skill-ID
- **Code**: Sollte die URL zu deinem Server weiterleiten

### Lambda-Code anzeigen:
Lambda → deine Funktion → Code-Tab → `lambda_function.py`

Der Code sollte ungefähr so aussehen:
```python
import json
import urllib.request

ENDPOINT = "https://<domain>/api/alexa/smart_home"

def lambda_handler(event, context):
    payload = json.dumps(event).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.loads(resp.read().decode("utf-8"))
```

### Konfiguration prüfen:
- **Timeout**: Muss mindestens 8-10 Sekunden sein
- **Memory**: 128 MB reicht
- **Trigger**: "Alexa Smart Home" mit Skill-ID

### Test in Lambda Console:
- Test-Tab → Neues Test-Event erstellen:
```json
{
  "directive": {
    "header": {
      "namespace": "Alexa.Discovery",
      "name": "Discover",
      "payloadVersion": "3",
      "messageId": "test-lambda-123"
    },
    "payload": {
      "scope": {
        "type": "BearerToken",
        "token": "dummy"
      }
    }
  }
}
```
- Ausführen → Response sollte 48 Endpoints enthalten

---

## 2. Alexa Developer Console prüfen

### Wo finden?
https://developer.amazon.com/alexa/console/ask

### Was prüfen?

#### a) Skill-Übersicht
- Deinen Skill finden (z.B. "Smart Home" oder wie du ihn benannt hast)
- Status: **Live** oder **Development**
- Type: Muss **Smart Home** sein (nicht Custom!)

#### b) Smart Home Service Endpoint
- Skill → Build Tab → "Smart Home" im Menü links
- **Default endpoint**: ARN deiner Lambda
  - Muss mit `arn:aws:lambda:` beginnen
  - Muss die **gleiche Region** sein wie deine Lambda

#### c) Account Linking
- Prüfe ob Account Linking konfiguriert ist
- Falls ja: Token-URL zeigt auf deinen HA → das erzeugt das JWT-Token im Log
- **Falls du HA nicht mehr brauchst**: Account Linking kann entfernt oder auf einen Dummy-OAuth umgestellt werden

#### d) Permissions
- Keine speziellen Permissions nötig für Smart Home Skills

---

## 3. Skill deaktivieren & neu aktivieren (Reset)

Das löst das Problem mit nicht gefundenen neuen Geräten:

### In der Alexa App (Handy):
1. **Mehr** (unten rechts im Menü)
2. **Skills & Spiele**
3. **Deine Skills** (Tab oben rechts)
4. **Entwickler-Skills** (Tab ganz rechts – dort erscheinen selbst erstellte Skills)
5. Deinen Skill antippen
6. **"Skill deaktivieren"** → bestätigen
7. 30 Sekunden warten
8. Gleicher Skill → **"Skill aktivieren"**
9. Alexa führt automatisch Discovery durch
10. Alexa sagt: "Ich habe X Geräte gefunden"

Danach sind alle Geräte aus der Discovery-Response frisch registriert.

### Alternativ per Sprache nach Reaktivierung:
```
"Alexa, suche nach neuen Geräten"
```

---

## 4. Account Linking (falls aktiv)

Wenn im Nginx-Log ein `BearerToken` (JWT) mitkommt, ist Account Linking aktiv. Das Token wurde ursprünglich von HA erzeugt.

### Optionen:

**A) Token ignorieren (aktuell)**  
Dein hc_alexa prüft das Token nicht → funktioniert.

**B) Account Linking entfernen**  
Developer Console → Skill → Account Linking → "Remove"  
Danach kommt kein Token mehr → saubererer Flow.

**C) Token validieren (Sicherheit)**  
Füge ein statisches Token in die `.env` und prüfe im Code ob es matcht.

---

## 5. Regionen-Checkliste

| Komponente | Region | URL |
|------------|--------|-----|
| Lambda | eu-west-1 (Ireland) | console.aws.amazon.com/lambda |
| Alexa Skill | EU/DE | developer.amazon.com/alexa/console/ask |
| Server | lokal | <domain.at> |

**Wichtig**: Lambda und Skill müssen in der gleichen Region sein!

Für Deutsche Alexa-Geräte:
- Skill-Region: EU (nicht US!)
- Lambda-Region: `eu-west-1` (Ireland) oder `eu-central-1` (Frankfurt)

---

## 6. Troubleshooting

| Problem | Ursache | Lösung |
|---------|---------|--------|
| Discovery kommt nicht an | Lambda Timeout | Lambda Timeout auf 10s erhöhen |
| "Keine neuen Geräte" | Gelöschte IDs gecached | Skill deaktivieren/aktivieren |
| "Gerät reagiert nicht" | ReportState fehlt/fehlerhaft | StateHandler prüfen |
| Token im Request | Account Linking aktiv | Ignorieren oder entfernen |
| Doppelte Geräte | Andere endpointId als vorher | IDs an HA-Format anpassen |

---

## 7. CloudWatch Logs (Lambda Debugging)

Lambda → Deine Funktion → Monitor-Tab → "CloudWatch Logs anzeigen"

Dort siehst du:
- Ob die Lambda aufgerufen wird
- Ob Timeout auftritt
- Ob der Response von deinem Server korrekt zurückkommt
- Fehler bei der HTTPS-Verbindung

---

In der Alexa App (Handy):

Mehr (unten rechts)
Skills & Spiele
Deine Skills (oben rechts Tab)
Entwickler-Skills (Tab ganz rechts – da erscheinen Skills die du in der Developer Console erstellt hast)
Deinen Skill finden und antippen
"Skill deaktivieren" → bestätigen
30 Sekunden warten
Gleicher Skill → "Skill aktivieren"
Alexa sagt "Ich habe X Geräte gefunden"

Account Linking – beim Aktivieren des Skills leitet Alexa dich zur HA Login-Seite um. 
Das Token das im Nginx-Log erscheint (BearerToken JWT) kommt genau daher.

Du hast zwei Optionen:

HA kurz starten nur für den Login, dann wieder stoppen – der Token bleibt gültig 
und die Geräte werden über hc_alexa bedient

Account Linking in der Developer Console entfernen – dann braucht der Skill keinen Login mehr. 
Aber: Du musst den Skill dann einmal neu aktivieren ohne Account Linking.

Für jetzt am einfachsten: Option 1 – HA starten, Skill deaktivieren/aktivieren (Login durchführen), 
HA wieder stoppen. Der Token ist dann gesetzt und alle Requests gehen weiterhin an hc_alexa via Nginx.

Langfristig solltest du das Account Linking in der Developer Console auf einen eigenen 
einfachen OAuth-Endpoint umstellen oder komplett entfernen.