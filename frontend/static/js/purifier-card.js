// frontend/static/js/purifier-card.js – Luftreiniger-Karte

const PURIFIER_MODES = [
    { value: 'Auto', label: 'Auto' },
    { value: 'Silent', label: 'Leise' },
    { value: 'Favorite', label: 'Turbo' },
];

export function renderPurifier(d) {
    const isOn = d.state === 'ON';
    const mode = d.mode || 'unknown';
    const aqi = d.aqi;
    const isOnline = d.state != null;

    // AQI-Qualitätsbewertung
    let aqiLabel = '–';
    let aqiClass = 'aqi-unknown';
    if (aqi != null) {
        if (aqi <= 12) { aqiLabel = 'Sehr gut'; aqiClass = 'aqi-good'; }
        else if (aqi <= 35) { aqiLabel = 'Gut'; aqiClass = 'aqi-moderate'; }
        else if (aqi <= 55) { aqiLabel = 'Mäßig'; aqiClass = 'aqi-unhealthy-sensitive'; }
        else if (aqi <= 150) { aqiLabel = 'Schlecht'; aqiClass = 'aqi-unhealthy'; }
        else { aqiLabel = 'Sehr schlecht'; aqiClass = 'aqi-hazardous'; }
    }

    const badgeClass = isOnline ? '' : 'offline';
    const badgeText = isOnline ? 'Online' : 'Offline';

    // Modus-Label normalisieren (python-miio gibt z.B. "OperationMode.Silent" zurück)
    const currentMode = mode.includes('.') ? mode.split('.').pop() : mode;

    const modeButtons = PURIFIER_MODES.map(m =>
        `<button class="purifier-mode-btn ${m.value === currentMode ? 'active' : ''}" data-mode="${m.value}" data-id="${d.id}">${m.label}</button>`
    ).join('');

    const powerClass = isOn ? 'purifier-on' : '';

    return `
    <div class="purifier-card ${powerClass}">
      <div class="purifier-header">
        <span class="purifier-state">
          <span class="dot ${isOn ? 'heating' : 'idle'}"></span>
          ${isOn ? 'Aktiv' : 'Aus'}
        </span>
        <span class="thermo-badge ${badgeClass}">${badgeText}</span>
      </div>
      <div class="purifier-aqi ${aqiClass}">
        <span class="purifier-aqi-value">${aqi != null ? aqi : '–'}</span>
        <span class="purifier-aqi-unit">µg/m³</span>
        <span class="purifier-aqi-label">${aqiLabel}</span>
      </div>
      <div class="purifier-power">
        <div class="switch-btn purifier-power-btn" data-action="power" data-id="${d.id}" data-state="${d.state || 'OFF'}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M12 2v6"/>
            <circle cx="12" cy="14" r="8"/>
          </svg>
        </div>
      </div>
      <div class="purifier-modes">${modeButtons}</div>
    </div>`;
}

export function initPurifierEvents(actionHandler) {
    // Power-Button
    document.querySelectorAll('.purifier-power-btn').forEach(el => {
        el.addEventListener('click', () => {
            const current = el.dataset.state;
            const next = current === 'ON' ? 'OFF' : 'ON';
            el.dataset.state = next;
            const card = el.closest('.purifier-card');
            if (next === 'ON') {
                card?.classList.add('purifier-on');
            } else {
                card?.classList.remove('purifier-on');
            }
            actionHandler(el.dataset.id, 'power', next);
        });
    });

    // Modus-Buttons
    document.querySelectorAll('.purifier-mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const group = btn.closest('.purifier-modes');
            group.querySelectorAll('.purifier-mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            actionHandler(btn.dataset.id, 'purifier_mode', btn.dataset.mode);
        });
    });
}
