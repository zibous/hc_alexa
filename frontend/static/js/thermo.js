// frontend/static/js/thermo.js – Thermostat-Karte

const MODES = [
    { value: 'off', label: 'Aus' },
    { value: 'heat', label: 'Heizen' },
    { value: 'auto', label: 'Auto' },
];

export function renderThermostat(d) {
    const setpoint = d.temperature ?? 20;
    const current = d.current_temp;
    const mode = d.system_mode || 'off';
    const isHeating = d.heating === 'ON' || mode === 'heat';
    const isOnline = d.last_seen != null || d.temperature != null;

    const stateText = isHeating ? 'Heizt...' : 'Standby';
    const dotClass = isHeating ? 'heating' : 'idle';
    const badgeClass = isOnline ? '' : 'offline';
    const badgeText = isOnline ? 'Online' : 'Offline';
    const currentText = current != null ? `Ist-Temperatur: ${current}°C` : '';

    const modeButtons = MODES.map(m =>
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
      <input type="range" class="thermo-slider" min="5" max="30" step="0.5" value="${setpoint}" data-action="temperature" data-id="${d.id}">
      <div class="thermo-modes">${modeButtons}</div>
    </div>`;
}

export function initThermostatEvents(actionHandler) {
    // Slider live update
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
            }, 400);
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
