// frontend/static/js/app.js – Einstiegspunkt
import { fetchDevices, sendCommand } from './api.js';
import { renderDevices } from './render.js';
import { initTheme } from './theme.js';

const POLL_INTERVAL = 30_000;
let devices = [];

async function loadDashboard() {
    try {
        devices = await fetchDevices();
        renderDevices(devices, handleAction);
        updateStatus(`${devices.length} Geräte · ${new Date().toLocaleTimeString('de-DE')}`);
    } catch (err) {
        updateStatus('Verbindung fehlgeschlagen');
        console.error('Ladefehler:', err);
    }
}

async function handleAction(deviceId, action, value) {
    try {
        await sendCommand(deviceId, action, value);
        // Lokalen State sofort updaten (kein Server-Refresh nötig)
        const device = devices.find(d => d.id === deviceId);
        if (device) {
            if (action === 'power') device.state = value;
            if (action === 'brightness') device.brightness = value;
            if (action === 'position') device.position = value;
            if (action === 'temperature') device.temperature = value;
            if (action === 'system_mode') device.system_mode = value;
        }
    } catch (err) {
        console.error('Steuerfehler:', err);
    }
}

function updateStatus(text) {
    const el = document.getElementById('headerStatus');
    if (el) el.textContent = text;
}

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    loadDashboard();
    setInterval(loadDashboard, POLL_INTERVAL);
});
