// frontend/static/js/theme.js – Theme Toggle
const KEY = 'alexa-theme';

export function initTheme() {
    const saved = localStorage.getItem(KEY) || 'dark';
    document.documentElement.setAttribute('data-theme', saved);

    const toggle = document.getElementById('themeToggle');
    if (toggle) {
        toggle.addEventListener('click', () => {
            const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem(KEY, next);
        });
    }
}
