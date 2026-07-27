#!/bin/bash
# Synchronisiert Z2M State-Dateien vom Remote-Host ins data/ Verzeichnis
# Wird vor dem Container-Start oder per Cronjob aufgerufen

REMOTE_HOST="nuc2020"
REMOTE_STATE="/docker/apps/zigbee2mqtt/data/state.json"
REMOTE_CONFIG="/docker/apps/zigbee2mqtt/data/configuration.yaml"
LOCAL_DIR="$(dirname "$0")/../data"

echo "Synchronisiere Z2M-Daten von $REMOTE_HOST..."

scp "$REMOTE_HOST:$REMOTE_STATE" "$LOCAL_DIR/z2m_state.json" 2>/dev/null \
    && echo "✅ state.json" \
    || echo "⚠️  state.json nicht erreichbar"

scp "$REMOTE_HOST:$REMOTE_CONFIG" "$LOCAL_DIR/z2m_config.yaml" 2>/dev/null \
    && echo "✅ configuration.yaml" \
    || echo "⚠️  configuration.yaml nicht erreichbar"
