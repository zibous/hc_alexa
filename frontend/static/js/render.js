// frontend/static/js/render.js – Orchestrierung & Event-Binding
import { renderDimmer, renderRoller, renderSensor, renderThermostat } from './cards.js';
import { icons } from './icons.js';
import { initLightEvents } from './light-card.js';
import { initRollerDrag } from './roller-drag.js';
import { initSwitchEvents, renderSwitch } from './switch-card.js';
import { initThermostatEvents } from './thermo.js';

let _actionHandler = null;

export function renderDevices(devices, actionHandler) {
  _actionHandler = actionHandler;
  const grid = document.getElementById('deviceGrid');
  if (!grid) return;

  // Nach Typ gruppieren
  const groups = {};
  const typeLabels = {
    roller: 'Rollläden',
    sensor: 'Temperatursensoren',
    thermostat: 'Heizungsthermostate',
    dimmer: 'Lichter',
    light: 'Lichter',
    switch: 'Schalter',
  };

  for (const d of devices) {
    const label = typeLabels[d.type] || d.type;
    if (!groups[label]) groups[label] = [];
    groups[label].push(d);
  }

  let html = '';
  for (const [label, items] of Object.entries(groups)) {
    html += `<div class="device-group">
      <h2 class="group-title">${label}</h2>
      <div class="device-grid-inner">${items.map(d => renderCard(d)).join('')}</div>
    </div>`;
  }

  grid.innerHTML = html;
  bindEvents();
  initRollerDrag(actionHandler);
  initThermostatEvents(actionHandler);
  initLightEvents(actionHandler);
  initSwitchEvents(actionHandler);
}

function renderCard(d) {
  const icon = icons[d.type] || icons.switch;
  const control = renderControl(d);

  return `
    <div class="device-card" data-id="${d.id}" data-type="${d.type}">
      <div class="device-card-header">
        <div>
          <div class="device-name">${icon} ${d.name}</div>
          <div class="device-type">${d.id}</div>
        </div>
        ${'' /* Toggle entfernt – Switches nutzen jetzt den Power-Button */}
      </div>
      ${control}
      <div class="device-status">${d.status || ''}</div>
    </div>`;
}

function renderControl(d) {
  switch (d.type) {
    case 'dimmer':
    case 'light': return renderDimmer(d);
    case 'roller': return renderRoller(d);
    case 'thermostat': return renderThermostat(d);
    case 'sensor': return renderSensor(d);
    case 'switch': return renderSwitch(d);
    default: return '';
  }
}

function bindEvents() {
  // Toggles (Power on/off)
  document.querySelectorAll('[data-action="power"]').forEach(el => {
    el.addEventListener('change', () => {
      _actionHandler(el.dataset.id, 'power', el.checked ? 'ON' : 'OFF');
    });
  });

  // Roller Buttons (Auf/Stop/Zu)
  document.querySelectorAll('[data-action="roller_cmd"]').forEach(el => {
    el.addEventListener('click', () => {
      // Aktiv-State anzeigen
      el.classList.add('active');
      setTimeout(() => el.classList.remove('active'), 1500);
      _actionHandler(el.dataset.id, 'roller_cmd', el.dataset.value);
    });
  });

  // Slider (debounced)
  document.querySelectorAll('input[type="range"]').forEach(el => {
    let timer;
    el.addEventListener('input', () => {
      const label = el.closest('.slider-control')?.querySelector('.slider-label span:last-child');
      const posLabel = el.closest('.device-card')?.querySelector('.roller-pos-badge');
      const suffix = el.dataset.action === 'temperature' ? '°C' : '%';
      if (label) label.textContent = `${el.value}${suffix}`;
      if (posLabel) posLabel.textContent = `${el.value}%`;
    });
    el.addEventListener('change', () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        _actionHandler(el.dataset.id, el.dataset.action, Number(el.value));
      }, 300);
    });
  });
}
