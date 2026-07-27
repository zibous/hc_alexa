// frontend/static/js/utils.js – Hilfsfunktionen

export function isStale(lastSeen) {
    if (!lastSeen) return false;
    const diff = Date.now() - new Date(lastSeen).getTime();
    return diff > 86400_000; // > 24 Stunden
}

export const SVG_STYLE = 'width:18px;height:18px;stroke:currentColor;stroke-width:2.5;fill:none;stroke-linecap:round;stroke-linejoin:round;display:block';
