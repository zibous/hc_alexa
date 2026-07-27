// frontend/static/js/light-card.js – Apple-Style Licht-Steuerung

export function renderLight(d) {
  const isOn = d.state === 'ON';
  const brightness = d.brightness ?? 0;
  // Shelly: 0-100, Z2M: 0-254 → normalisieren auf 0-100%
  const maxBri = (d.protocol === 'z2m') ? 254 : 100;
  const pct = Math.round((brightness / maxBri) * 100);
  const glowClass = isOn ? 'light-on' : '';
  const iconOpacity = isOn ? 1 : 0.3;

  return `
    <div class="light-card ${glowClass}">
      <div class="light-bulb" data-action="power" data-id="${d.id}" data-state="${isOn ? 'ON' : 'OFF'}">
        <svg style="width:48px;height:48px;opacity:${iconOpacity}" viewBox="0 0 24 24" fill="none" stroke="${isOn ? '#fbbf24' : 'var(--text-muted)'}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 18h6M10 22h4"/>
          <path d="M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z" fill="${isOn ? 'rgba(251,191,36,.15)' : 'none'}"/>
        </svg>
      </div>
      <div class="light-info">
        <span class="light-pct">${pct}%</span>
      </div>
      <input type="range" class="light-slider" min="0" max="${maxBri}" value="${brightness}" data-action="brightness" data-id="${d.id}" data-max="${maxBri}">
    </div>`;
}

export function initLightEvents(actionHandler) {
  // Bulb Toggle (An/Aus) – sofortiges visuelles Feedback
  document.querySelectorAll('.light-bulb').forEach(el => {
    el.addEventListener('click', () => {
      const current = el.dataset.state;
      const next = current === 'ON' ? 'OFF' : 'ON';
      el.dataset.state = next;

      const card = el.closest('.device-card');
      const lightCard = card?.querySelector('.light-card');
      const pctLabel = card?.querySelector('.light-pct');
      if (next === 'ON') {
        lightCard?.classList.add('light-on');
      } else {
        lightCard?.classList.remove('light-on');
        if (pctLabel) pctLabel.textContent = 'Aus';
      }

      actionHandler(el.dataset.id, 'power', next);
    });
  });

  // Brightness Slider
  document.querySelectorAll('.light-slider').forEach(el => {
    let timer;
    el.addEventListener('input', () => {
      const card = el.closest('.device-card');
      const pctLabel = card?.querySelector('.light-pct');
      const max = Number(el.dataset.max || 100);
      const pct = Math.round((el.value / max) * 100);
      if (pctLabel) pctLabel.textContent = `${pct}%`;
    });
    el.addEventListener('change', () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        actionHandler(el.dataset.id, 'brightness', Number(el.value));
      }, 300);
    });
  });
}
