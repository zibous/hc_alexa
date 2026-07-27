// frontend/static/js/switch-card.js – Apple-Style Power Switch

export function renderSwitch(d) {
    const isOn = d.state === 'ON';
    const glowClass = isOn ? 'switch-on' : '';

    return `
    <div class="switch-card ${glowClass}">
      <div class="switch-btn" data-action="power" data-id="${d.id}" data-state="${d.state || 'OFF'}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M12 2v6"/>
          <circle cx="12" cy="14" r="8"/>
        </svg>
      </div>
      <span class="switch-label">${isOn ? 'Ein' : 'Aus'}</span>
    </div>`;
}

export function initSwitchEvents(actionHandler) {
    document.querySelectorAll('.switch-btn').forEach(el => {
        el.addEventListener('click', () => {
            const current = el.dataset.state;
            const next = current === 'ON' ? 'OFF' : 'ON';
            el.dataset.state = next;

            const card = el.closest('.device-card');
            const switchCard = card?.querySelector('.switch-card');
            const label = card?.querySelector('.switch-label');

            if (next === 'ON') {
                switchCard?.classList.add('switch-on');
                if (label) label.textContent = 'Ein';
            } else {
                switchCard?.classList.remove('switch-on');
                if (label) label.textContent = 'Aus';
            }

            actionHandler(el.dataset.id, 'power', next);
        });
    });
}
