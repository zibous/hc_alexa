// frontend/static/js/thermo.js – Thermostat-Karte

const MODES_HEATING = [
    { value: 'off', label: 'Aus' },
    { value: 'heat', label: 'Heizen' },
    { value: 'auto', label: 'Auto' },
];

const MODES_AC = [
    { value: 'off', label: 'Aus' },
    { value: 'cool', label: 'Kühlen' },
    { value: 'auto', label: 'Auto' },
];

export function renderThermostat(d) {
    const setpoint = d.temperature ?? 20;
    const current = d.current_temp;
    const mode = d.system_mode || 'off';
    const isAC = d.protocol === 'midea';
    const isActive = isAC ? (mode !== 'off' && d.state === 'ON') : (d.heating === 'ON' || mode === 'heat');
    const isOnline = d.last_seen != null || d.temperature != null;

    const stateText = isAC
        ? (isActive ? (mode === 'cool' ? 'Kühlt...' : mode === 'heat' ? 'Heizt...' : 'Aktiv') : 'Standby')
        : (isActive ? 'Heizt...' : 'Standby');
    const dotClass = isActive ? 'heating' : 'idle';
    const badgeClass = isOnline ? '' : 'offline';
    const badgeText = isOnline ? 'Online' : 'Offline';
    const currentText = current != null ? `Ist-Temperatur: ${current}°C` : '';

    const modes = isAC ? MODES_AC : MODES_HEATING;
    const modeButtons = modes.map(m =>
        `<button class="thermo-mode-btn ${m.value === mode ? 'active' : ''}" data-mode="${m.value}" data-id="${d.id}">${m.label}</button>`
    ).join('');

    return `
    <div class="thermo-card">
      <div class="thermo-header">
        <span class="thermo-state"><span class="dot ${dotClass}"></span>${stateText}</span>
        <span class="thermo-badge ${badgeClass}">${badgeText}</span>
      </div>
      <div class="thermo-setpoint">${setpoint}°C</div>
      <div class="thermo-current">${currentText}</div>
      <input type="range" class="thermo-slider" min="${isAC ? 16 : 5}" max="30" step="${isAC ? 1 : 0.5}" value="${setpoint}" data-action="temperature" data-id="${d.id}">
      <div class="thermo-modes">${modeButtons}</div>
    </div>`;
}

export function initThermostatEvents(actionHandler) {
    // Slider live update mit Debounce (1.5s – Midea braucht Zeit zwischen Befehlen)
    document.querySelectorAll('.thermo-slider').forEach(el => {
        let timer;
        el.addEventListener('input', () => {
            const card = el.closest('.device-card');
            const label = card?.querySelector('.thermo-setpoint');
            if (label) label.textContent = `${el.value}°C`;
        });
        el.addEventListener('change', () => {
            clearTimeout(timer);
            timer = setTimeout(() => {
                actionHandler(el.dataset.id, 'temperature', Number(el.value));
            }, 1500);
        });
    });

    // Mode Buttons
    document.querySelectorAll('.thermo-mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const group = btn.closest('.thermo-modes');
            group.querySelectorAll('.thermo-mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            actionHandler(btn.dataset.id, 'system_mode', btn.dataset.mode);
        });
    });
}
