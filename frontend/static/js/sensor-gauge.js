// frontend/static/js/sensor-gauge.js – Kreisförmige Temperatur-Anzeige
import { isStale } from './utils.js';

const MIN_TEMP = 0;
const MAX_TEMP = 40;

export function renderSensor(d) {
  const temp = d.temperature ?? null;
  const unit = d.unit || '°C';
  const stale = isStale(d.last_seen);
  const dotClass = stale ? 'status-dot stale' : 'status-dot live';

  if (temp === null) {
    return `<div class="sensor-gauge">
      <span class="${dotClass}"></span>
      <div class="gauge-value">–${unit}</div>
    </div>`;
  }

  // Nicht-Temperatur: Zähler-Display
  if (unit !== '°C') {
    return renderCounter(temp, unit, dotClass);
  }

  // Temperatur: Ring-Gauge
  const pct = Math.max(0, Math.min(100, ((temp - MIN_TEMP) / (MAX_TEMP - MIN_TEMP)) * 100));
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  let color = '#06d6a0';
  if (temp > 30) color = 'var(--red)';
  else if (temp < 10) color = '#48bfe3';

  return `
    <div class="sensor-gauge">
      <span class="${dotClass}"></span>
      <svg class="gauge-ring" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="${radius}" fill="none" stroke="var(--border)" stroke-width="8"/>
        <circle cx="60" cy="60" r="${radius}" fill="none" stroke="${color}" stroke-width="8"
                stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"
                stroke-linecap="round" transform="rotate(-90 60 60)"/>
      </svg>
      <div class="gauge-value">${temp}${unit}</div>
    </div>`;
}

function renderCounter(value, unit, dotClass) {
  // Zahl in einzelne Ziffern aufteilen (mit Dezimalpunkt)
  const formatted = Number(value).toFixed(2);
  const [whole, decimal] = formatted.split('.');
  const digits = whole.padStart(5, '0').split('');

  const digitHtml = digits.map(d =>
    `<span class="counter-digit">${d}</span>`
  ).join('') +
    `<span class="counter-sep">.</span>` +
    decimal.split('').map(d =>
      `<span class="counter-digit counter-decimal">${d}</span>`
    ).join('');

  return `
    <div class="counter-display">
      <span class="${dotClass}"></span>
      <div class="counter-digits">${digitHtml}</div>
      <div class="counter-unit">${unit}</div>
    </div>`;
}
