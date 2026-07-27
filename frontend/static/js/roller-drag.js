// frontend/static/js/roller-drag.js – Drag-to-Position für Rollladen-SVG

export function initRollerDrag(actionHandler) {
    document.querySelectorAll('.roller-window-wrap').forEach(wrap => {
        const svg = wrap.querySelector('svg');
        const card = wrap.closest('.device-card');
        if (!svg || !card) return;

        const deviceId = card.dataset.id;
        const cloth = svg.querySelector('.roller-cloth');
        const bar = svg.querySelector('.roller-bar');
        const handle = svg.querySelector('.roller-handle');
        const label = wrap.querySelector('.roller-pos-badge');

        if (!cloth || !handle) return;

        let dragging = false;
        const minY = 18;  // Stoff-Start (ganz offen)
        const maxY = 120; // Stoff-Ende (ganz zu)

        function posFromY(y) {
            const clamped = Math.max(minY, Math.min(maxY, y));
            // y=18 → 100% (offen), y=120 → 0% (zu)
            return Math.round(100 - ((clamped - minY) / (maxY - minY)) * 100);
        }

        function yFromPos(pos) {
            return minY + ((100 - pos) / 100) * (maxY - minY);
        }

        function updateVisual(y) {
            const clothH = y - minY;
            cloth.setAttribute('height', clothH);
            if (bar) {
                bar.setAttribute('y', y - 4);
            }
            handle.setAttribute('cy', y + 4);

            const pos = posFromY(y);
            if (label) label.textContent = `${pos}%`;
        }

        function getSvgY(e) {
            const pt = svg.createSVGPoint();
            const touch = e.touches ? e.touches[0] : e;
            pt.x = touch.clientX;
            pt.y = touch.clientY;
            const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());
            return svgP.y;
        }

        // Mouse/Touch Events
        handle.style.cursor = 'ns-resize';
        cloth.style.cursor = 'ns-resize';

        function startDrag(e) {
            e.preventDefault();
            dragging = true;
            wrap.classList.add('dragging');
        }

        function moveDrag(e) {
            if (!dragging) return;
            e.preventDefault();
            const y = getSvgY(e);
            updateVisual(y);
        }

        function endDrag(e) {
            if (!dragging) return;
            dragging = false;
            wrap.classList.remove('dragging');
            const y = getSvgY(e.changedTouches ? e.changedTouches[0] : e);
            const pos = posFromY(y);
            actionHandler(deviceId, 'position', pos);
        }

        // Mouse
        handle.addEventListener('mousedown', startDrag);
        cloth.addEventListener('mousedown', startDrag);
        document.addEventListener('mousemove', moveDrag);
        document.addEventListener('mouseup', endDrag);

        // Touch
        handle.addEventListener('touchstart', startDrag, { passive: false });
        cloth.addEventListener('touchstart', startDrag, { passive: false });
        document.addEventListener('touchmove', moveDrag, { passive: false });
        document.addEventListener('touchend', endDrag);
    });
}
