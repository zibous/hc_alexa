# Schritt 1: Das manipulierte AWS Lambda-Skript
# Ersetzen Sie den Code Ihrer AWS Lambda-Funktion durch dieses Skript.
# Es fängt die Login-Anfrage (Alexa.Authorization) von Amazon ab und beantwortet sie
# direkt in der Cloud mit einem Fake-Erfolg, ohne Ihren Server überhaupt zu fragen.

import json
import urllib.request

def lambda_handler(event, context):
    # DIE ADRESSE ZU IHREM EIGENEN PYTHON-SKRIPT (ÜBER NGINX)
    target_url = "https://ihre-domain.de"

    # 1. TRICK: Alexa bittet um Bestätigung der Kontoverknüpfung
    # Wir sagen einfach sofort "JA", ohne dass ein echter Login stattfand.
    namespace = event.get('directive', {}).get('header', {}).get('namespace', '')
    if namespace == 'Alexa.Authorization':
        return {
            "event": {
                "header": {
                    "namespace": "Alexa.Authorization",
                    "name": "AcceptGrant.Response",
                    "messageId": event['directive']['header']['messageId'],
                    "payloadVersion": "3"
                },
                "payload": {}
            }
        }

    # 2. NORMAER TRANSPORT: Alle anderen Befehle (Licht an/aus) gehen an Ihr Python-Skript
    headers = {'Content-Type': 'application/json'}
    req = urllib.request.Request(target_url, data=json.dumps(event).encode('utf-8'), headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Fehler: Python-Skript nicht erreichbar: {e}")
        return {}


# Schritt 2: Fake-Daten in der Amazon Developer Console
# Da Amazon zwingend Textfelder beim Account Linking verlangt,
# füttern wir die Maske mit funktionierenden Fake-URLs.
# Alexa wird diese durch unseren Lambda-Trick niemals real aufrufen.
# Tragen Sie in der Developer Console unter Account Linking einfach Folgendes ein:
# Authorization URI: https://google.com (Igendeine HTTPS-Adresse)
# Access Token URI:  https://google.com
# Client ID: mein_geheimer_python_schluessel (Frei wählbar)
# Client Secret: super_sicheres_passwort_123 (Frei wählbar)
# Client Authentication Scheme: Credentials in request body
# Scope: Klicken Sie auf Add scope und tippen Sie smart_home ein.
# Klicken Sie auf Save.

# Schritt 3: Aktivierung in der Alexa App
# Öffnen Sie die Alexa App auf dem Smartphone.
# Gehen Sie auf Mehr
#    ➡️ Skills und Spiele
#    ➡️ Ihre Skills
#    ➡️ Entwickler.
# Wählen Sie Ihren Skill und klicken Sie auf Zur Verwendung aktivieren.
# Was jetzt passiert:
# Es öffnet sich ganz kurz ein Fenster (z. B. Google oder eine leere Seite) und schließt sich sofort wieder.
# Die App meldet: "Der Skill wurde erfolgreich verknüpft!"

# Schritt 4: Ihr Python-Empfänger-Skript (Ohne OAuth)
# Ihr Python-Skript (das hinter Nginx läuft) muss sich jetzt um keinerlei Absicherung oder Token-Prüfung mehr kümmern.
# Es lauscht nur auf die reinen Steuerbefehle.
# Sie können das Flask-Skript aus der vorherigen Antwort eins zu eins nutzen.

