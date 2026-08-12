// frontend/static/js/icons.js – Geräte-Icons (inline SVG)
const svg = (path) => `<svg style="width:16px;height:16px;vertical-align:-2px;stroke:currentColor;stroke-width:2;fill:none;display:inline" viewBox="0 0 24 24">${path}</svg>`;

export const icons = {
    switch: svg('<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>'),
    dimmer: svg('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>'),
    roller: svg('<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18"/>'),
    thermostat: svg('<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>'),
    sensor: svg('<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/><path d="M10 13V4"/>'),
    purifier: svg('<path d="M8 2h8l2 4H6l2-4Z"/><rect x="6" y="6" width="12" height="14" rx="2"/><circle cx="12" cy="13" r="3"/><path d="M12 10v-1M9.5 11.5l-.7-.7M14.5 11.5l.7-.7"/>'),
};
