// frontend/static/js/api.js – API-Aufrufe
const BASE = 'api';

export async function fetchDevices() {
    const res = await fetch(`${BASE}/devices`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function sendCommand(deviceId, action, value) {
    const res = await fetch(`${BASE}/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ device_id: deviceId, action, value }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}
