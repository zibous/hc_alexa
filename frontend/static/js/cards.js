// frontend/static/js/cards.js – Karten-Templates pro Gerätetyp

export function renderToggle(d) {
  const checked = d.state === 'ON' ? 'checked' : '';
  return `
    <label class="toggle">
      <input type="checkbox" data-action="power" data-id="${d.id}" ${checked}>
      <span class="toggle-track"></span>
      <span class="toggle-thumb"></span>
    </label>`;
}

export { renderLight as renderDimmer } from './light-card.js';

export function renderRoller(d) {
  const val = d.position ?? 100;
  const clothY = 18 + Math.round((100 - val) * 1.02);
  const svgBtn = 'width:22px;height:22px;stroke:currentColor;stroke-width:2.5;fill:none;stroke-linecap:round;stroke-linejoin:round;display:block';

  const windowSvg = `
    <svg viewBox="0 0 160 140" style="width:100%;height:140px;display:block;touch-action:none">
      <rect x="20" y="14" width="120" height="120" rx="3" fill="none" stroke="var(--border)" stroke-width="2"/>
      <line x1="80" y1="14" x2="80" y2="134" stroke="var(--border)" stroke-width="1.5"/>
      <rect x="132" y="62" width="4" height="16" rx="1" fill="none" stroke="var(--text-muted)" stroke-width="1.5"/>
      <rect x="18" y="10" width="124" height="10" rx="5" fill="var(--text-muted)" opacity=".4"/>
      <rect class="roller-cloth" x="22" y="18" width="116" height="${clothY - 18}" rx="1" fill="var(--text-muted)" opacity=".4"/>
      <rect class="roller-bar" x="22" y="${clothY - 4}" width="116" height="5" rx="2" fill="var(--text-muted)" opacity=".6"/>
      <line x1="80" y1="${clothY + 4}" x2="80" y2="134" stroke="var(--text-muted)" stroke-width="1" opacity=".4"/>
      <circle class="roller-handle" cx="80" cy="${clothY + 4}" r="6" fill="var(--accent)" opacity=".8"/>
    </svg>`;

  return `
    <div class="roller-visual">
      <div class="roller-buttons-col">
        <span class="btn-roller" data-action="roller_cmd" data-id="${d.id}" data-value="open" title="Auf"><svg style="${svgBtn}" viewBox="0 0 24 24"><path d="M12 19V5M5 12l7-7 7 7"/></svg></span>
        <span class="btn-roller" data-action="roller_cmd" data-id="${d.id}" data-value="stop" title="Stop"><svg style="${svgBtn}" viewBox="0 0 24 24"><rect x="7" y="7" width="10" height="10" rx="1"/></svg></span>
        <span class="btn-roller" data-action="roller_cmd" data-id="${d.id}" data-value="close" title="Zu"><svg style="${svgBtn}" viewBox="0 0 24 24"><path d="M12 5v14M5 12l7 7 7-7"/></svg></span>
      </div>
      <div class="roller-window-wrap">
        ${windowSvg}
        <div class="roller-pos-badge">${val}%</div>
      </div>
    </div>
    `;
}

export { renderThermostat } from './thermo.js';

export { renderSensor } from './sensor-gauge.js';
