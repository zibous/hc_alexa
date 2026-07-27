# Variablen

PROJECT_NAME = $(notdir $(CURDIR))
FORGEJO_IP   = 10.1.1.119
FORGEJO_PORT = 3143
FORGEJO_USER = peter
FORGEJO_URL  = http://$(FORGEJO_IP):$(FORGEJO_PORT)/$(FORGEJO_USER)/$(PROJECT_NAME).git

APP_NAME = alexa_fastapi

SHELL := /bin/bash
.DEFAULT_GOAL := help
.PHONY: build up down

.PHONY: up down restart build logs test-discovery test-power-on test-power-off test-roller test-health
 
 VERSION := $(shell git describe --tags --always)

# ---------------------------------------------------------
# Lokales Ausführen (Dev ohne Docker)
# ---------------------------------------------------------
dev: ## Startet lokal mit auto-reload (ohne Docker)
	@echo "Starte Dev-Server: http://10.1.1.119:5018/dashboard/"
	@PYTHONPATH=$(CURDIR) python3 -m uvicorn app.main:app --host 0.0.0.0 --port 5018 --reload

# ---------------------------------------------------------
# Docker
# ---------------------------------------------------------

check-config: ## YAML-Syntax und Struktur prüfen
	docker compose config

check-build: ## Simuliert den Build-Prozess (Trockenlauf)
	docker compose --dry-run up --build -d

check-dockerfiles: # Nutzt den schnellen Buildkit-Check für alle Dockerfiles im Compose-File
	BUILDKIT_DOCKERFILE_CHECK=1 docker compose build

check-buildall: config check-dockerfiles
	@echo "✅ Alles sieht gut aus! Bereit für den echten Build."

sync-z2m: ## Z2M State-Dateien vom Remote-Host holen
	@./scripts/sync_z2m.sh

up: sync-z2m ## Start containers (mit Z2M-Sync)
	docker compose up -d

down: ## Stop containers
	@echo "Stop containers"
	docker compose down


restart: sync-z2m ## Restart containers (mit Z2M-Sync)
	docker compose restart

rebuild: sync-z2m ## Rebuild and restart (no cache)
	docker compose down
	docker compose build --no-cache
	docker compose up -d --force-recreate

build: sync-z2m
	docker compose up -d --build

logs:
	docker compose logs -f

logs-tail: ## Last 100 log lines
	docker compose logs --tail=100

ps: ## Running containers
	docker compose ps

stop: ## Stop containers
	docker compose stop

start: ## Start stopped containers
	docker compose start

shell: ## Shell into container
	docker compose exec $(CONTAINER) /bin/bash

# ---------------------------------------------------------
# Maintenance
# ---------------------------------------------------------
install: ## Install dependencies
	@pip install -r requirements.txt

jsbuild: ## 🔧 Komprimiert JS und CSS parallel über Docker – maximal optimiert
	@echo "📦 Starte JS & CSS Bundling via Docker & esbuild..."
	@cp ../shared/themes/theme.css frontend/static/css/theme.css
	@docker run --rm -v "$$(pwd)":/app -w /app node:20-alpine sh -c "\
		npx esbuild frontend/static/js/app.js --bundle --minify --sourcemap --target=es2020 --outfile=frontend/static/js/app.bundle.js && \
		npx esbuild frontend/static/css/style.css --bundle --minify --sourcemap --outfile=frontend/static/css/style.bundle.css"
	@echo "✅ Fertig!"

jsclean: ## 🔧 Komprimiert JS und CSS entfernen
	@echo "🧼 Bereinige produktive Build-Dateien..."
	@rm -f frontend/static/js/app.bundle.js
	@rm -f frontend/static/js/app.bundle.js.map
	@rm -f frontend/static/css/style.bundle.css
	@rm -f frontend/static/css/style.bundle.css.map
	@echo "✨ Verzeichnis ist wieder sauber."

git-status: ## Zeigt die aktuelle Forgejo Server-Verbindung (Remote URL) an
	@echo "🔍 Überprüfe Git-Remote-Konfiguration..."
	@if ! git remote get-url origin >/dev/null 2>&1; then \
		echo "❌ Fehler: 'origin' ist noch nicht eingerichtet!"; \
		echo "👉 Bitte führe aus: make git-setup"; \
		exit 1; \
	fi
	@URL=$$(git remote get-url origin); \
	echo "🍏 Forgejo-Server ist aktiv verbunden!" ; \
	echo "🔗 Aktuelle URL: $$URL"

git-setup: ## Git-Verbindung zum Forgejo-Server automatisch einrichten oder korrigieren
	@echo "🛠️ Initialisiere Forgejo Server-Verbindung für '$(PROJECT_NAME)'..."
	@if ! git remote get-url origin >/dev/null 2>&1; then \
		git remote add origin $(FORGEJO_URL); \
		echo "🎉 Server-URL erfolgreich neu angelegt!"; \
	else \
		git remote set-url origin $(FORGEJO_URL); \
		echo "🔄 Bestehende Server-URL erfolgreich korrigiert!"; \
	fi
	@echo "🔗 Ziel-Adresse: $(FORGEJO_URL)"

git-update: git-status ## Git Forgejo Update durchführen (Normaler Zwischenstand)
	git add -A
	git commit -m "Update am $$(date +'%Y-%m-%d %H:%M')" || true
	git push -u origin main

git-release: git-status ## Neues Versions-Tag automatisch berechnen, erstellen und zu Forgejo pushen
	git add -A
	git commit -m "Release-Vorbereitung am $$(date +'%Y-%m-%d %H:%M')" || true
	git push origin main
	@LAST_TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo "v2.1.0"); \
	NEXT_TAG=$$(echo $$LAST_TAG | awk -F. '{print $$1"."$$2"."$$3+1}'); \
	echo "🍏 Letzte Version war: $$LAST_TAG"; \
	echo "⚡ Berechnete neue Version: $$NEXT_TAG"; \
	echo "📦 Erstelle Git-Tag $$NEXT_TAG mit aktuellem Zeitstempel..."; \
	git tag -a $$NEXT_TAG -m "Automatisches Release $$NEXT_TAG am $$(date +'%Y-%m-%d %H:%M') via Makefile"; \
	git push origin $$NEXT_TAG; \
	echo "🎉 Version $$NEXT_TAG erfolgreich an Forgejo übermittelt!"


# --- TEST BEFEHLE (simuliert AWS Lambda → FastAPI) ---
HOST := 10.1.1.119
PORT := 5018
URL := http://$(HOST):$(PORT)/api/alexa/smart_home

test-discovery: ## Alexa Discovery simulieren (Geräteliste)
	@curl -s -X POST $(URL) \
		-H "Content-Type: application/json" \
		-d '{"directive":{"header":{"namespace":"Alexa.Discovery","name":"Discover","payloadVersion":"3","messageId":"test-1234"}}}' | python3 -m json.tool

test-power-on: ## Schalter einschalten (Gartenbrunnen)
	@curl -s -X POST $(URL) \
		-H "Content-Type: application/json" \
		-d '{"directive":{"header":{"namespace":"Alexa.PowerController","name":"TurnOn","payloadVersion":"3","messageId":"t-001","correlationToken":"ct-001"},"endpoint":{"endpointId":"wasserbrunnen"},"payload":{}}}' | python3 -m json.tool

test-power-off: ## Schalter ausschalten (Gartenbrunnen)
	@curl -s -X POST $(URL) \
		-H "Content-Type: application/json" \
		-d '{"directive":{"header":{"namespace":"Alexa.PowerController","name":"TurnOff","payloadVersion":"3","messageId":"t-002","correlationToken":"ct-002"},"endpoint":{"endpointId":"wasserbrunnen"},"payload":{}}}' | python3 -m json.tool

test-roller: ## Rollladen auf 50% (Küche)
	@curl -s -X POST $(URL) \
		-H "Content-Type: application/json" \
		-d '{"directive":{"header":{"namespace":"Alexa.RangeController","name":"SetRangeValue","payloadVersion":"3","messageId":"t-003","correlationToken":"ct-003"},"endpoint":{"endpointId":"rollladen_kueche"},"payload":{"rangeValue":50}}}' | python3 -m json.tool

test-dimmer: ## Dimmer auf 70% (Küche)
	@curl -s -X POST $(URL) \
		-H "Content-Type: application/json" \
		-d '{"directive":{"header":{"namespace":"Alexa.BrightnessController","name":"SetBrightness","payloadVersion":"3","messageId":"t-004","correlationToken":"ct-004"},"endpoint":{"endpointId":"lichtdimmer_kueche"},"payload":{"brightness":70}}}' | python3 -m json.tool

test-thermostat: ## Thermostat auf 22°C (Bad)
	@curl -s -X POST $(URL) \
		-H "Content-Type: application/json" \
		-d '{"directive":{"header":{"namespace":"Alexa.ThermostatController","name":"SetTargetSetpoint","payloadVersion":"3","messageId":"t-005","correlationToken":"ct-005"},"endpoint":{"endpointId":"thermostat_bad"},"payload":{"targetSetpoint":{"value":22.0,"scale":"CELSIUS"}}}}' | python3 -m json.tool

test-sensor: ## Temperatursensor abfragen (Nordseite)
	@curl -s -X POST $(URL) \
		-H "Content-Type: application/json" \
		-d '{"directive":{"header":{"namespace":"Alexa","name":"ReportState","payloadVersion":"3","messageId":"t-006","correlationToken":"ct-006"},"endpoint":{"endpointId":"weather_outnorth_temperature"},"payload":{}}}' | python3 -m json.tool

test-esphome: ## ESPHome Türöffner einschalten
	@curl -s -X POST $(URL) \
		-H "Content-Type: application/json" \
		-d '{"directive":{"header":{"namespace":"Alexa.PowerController","name":"TurnOn","payloadVersion":"3","messageId":"t-007","correlationToken":"ct-007"},"endpoint":{"endpointId":"turoffner"},"payload":{}}}' | python3 -m json.tool

test-dashboard: ## Dashboard API: Geräteliste
	@curl -s http://$(HOST):$(PORT)/dashboard/api/devices | python3 -m json.tool

test-health: ## Health-Check
	@curl -s http://$(HOST):$(PORT)/health | python3 -m json.tool


# ---------------------------------------------------------
# Help
# ---------------------------------------------------------
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
