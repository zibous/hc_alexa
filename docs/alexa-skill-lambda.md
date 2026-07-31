OK – Schritt für Schritt:

1. Neuen Skill erstellen
Öffne https://developer.amazon.com/alexa/console/ask
User + Passwort wie Amazon Shop Account
Create Skill
Einstellungen:
Name: Mein Zuhause (oder was du willst)
Primary locale: German (DE)
Type of experience: Smart Home
Hosting: Provision your own
Next → Create Skill
amzn1.ask.skill.2326a427-d619-45f9-a2a9-78e6d0a58d80


2. Smart Home Endpoint setzen
Im Skill → links im Menü: Smart Home
Smart Home service endpoint:
Default endpoint: Die ARN deiner bestehenden Lambda
  arn:aws:lambda:eu-west-1:698494875144:function:Homeassistant
Save


3. Lambda Trigger aktualisieren
AWS Console → Lambda → deine Funktion
Trigger hinzufügen → "Alexa Smart Home"
Skill ID: 
Die neue Skill-ID kopieren (steht oben im Skill: amzn1.ask.skill.xxxxxxxx)

Add
Hinweis: Die Lambda kann mehrere Skill-Triggers haben – der alte Skill bleibt erstmal auch dran.

4. Kein Account Linking
Im neuen Skill: Account Linking → NICHT konfigurieren
Einfach leer lassen → kein Login nötig

5. Skill aktivieren
Alexa App → Mehr → Skills → Deine Skills → Entwickler
Der neue Skill "Mein Zuhause" erscheint
Aktivieren (kein Login-Screen!)
Alexa sagt: "Ich habe X Geräte gefunden"
Fang mit Schritt 1 an und sag mir wenn du bei einem Schritt hängst.