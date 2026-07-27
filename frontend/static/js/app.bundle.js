(()=>{var d="dashboard/api";async function l(){let e=await fetch(`${d}/devices`);if(!e.ok)throw new Error(`HTTP ${e.status}`);return e.json()}async function p(e,t,n){let a=await fetch(`${d}/control`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({device_id:e,action:t,value:n})});if(!a.ok)throw new Error(`HTTP ${a.status}`);return a.json()}var i=e=>`<svg style="width:16px;height:16px;vertical-align:-2px;stroke:currentColor;stroke-width:2;fill:none;display:inline" viewBox="0 0 24 24">${e}</svg>`,r={switch:i('<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>'),dimmer:i('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>'),roller:i('<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18"/>'),thermostat:i('<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>'),sensor:i('<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/><path d="M10 13V4"/>')};var s=null;function m(e,t){s=t;let n=document.getElementById("deviceGrid");n&&(n.innerHTML=e.map(a=>f(a)).join(""),x(e))}function f(e){let t=r[e.type]||r.switch,n=$(e);return`
    <div class="device-card" data-id="${e.id}" data-type="${e.type}">
      <div class="device-card-header">
        <div>
          <div class="device-name">${t} ${e.name}</div>
          <div class="device-type">${e.device} \xB7 ${e.type}</div>
        </div>
        ${e.type==="switch"||e.type==="dimmer"?y(e):""}
      </div>
      ${n}
      <div class="device-status">${e.status||""}</div>
    </div>`}function y(e){let t=e.state==="ON"?"checked":"";return`
    <label class="toggle">
      <input type="checkbox" data-action="power" data-id="${e.id}" ${t}>
      <span class="toggle-track"></span>
      <span class="toggle-thumb"></span>
    </label>`}function $(e){if(e.type==="dimmer"){let t=e.brightness??50;return`
      <div class="slider-control">
        <input type="range" min="0" max="100" value="${t}" data-action="brightness" data-id="${e.id}">
        <div class="slider-label"><span>Helligkeit</span><span>${t}%</span></div>
      </div>`}if(e.type==="roller"){let t=e.position??100;return`
      <div class="slider-control">
        <input type="range" min="0" max="100" value="${t}" data-action="position" data-id="${e.id}">
        <div class="slider-label"><span>Position</span><span>${t}%</span></div>
      </div>`}if(e.type==="thermostat"){let t=e.temperature??20;return`
      <div class="slider-control">
        <input type="range" min="5" max="30" step="0.5" value="${t}" data-action="temperature" data-id="${e.id}">
        <div class="slider-label"><span>Soll-Temp</span><span>${t}\xB0C</span></div>
      </div>`}return e.type==="sensor"?`<div class="device-status" style="font-size:1.4rem;font-weight:700;color:var(--accent)">${e.temperature??"\u2013"}\xB0C</div>`:""}function x(e){document.querySelectorAll('[data-action="power"]').forEach(t=>{t.addEventListener("change",()=>{s(t.dataset.id,"power",t.checked?"ON":"OFF")})}),document.querySelectorAll('input[type="range"]').forEach(t=>{let n;t.addEventListener("input",()=>{let a=t.closest(".slider-control")?.querySelector(".slider-label span:last-child"),g=t.dataset.action==="temperature"?"\xB0C":"%";a&&(a.textContent=`${t.value}${g}`)}),t.addEventListener("change",()=>{clearTimeout(n),n=setTimeout(()=>{s(t.dataset.id,t.dataset.action,Number(t.value))},300)})})}var u="alexa-theme";function v(){let e=localStorage.getItem(u)||"dark";document.documentElement.setAttribute("data-theme",e);let t=document.getElementById("themeToggle");t&&t.addEventListener("click",()=>{let n=document.documentElement.getAttribute("data-theme")==="dark"?"light":"dark";document.documentElement.setAttribute("data-theme",n),localStorage.setItem(u,n)})}var b=3e4,o=[];async function c(){try{o=await l(),m(o,w),h(`${o.length} Ger\xE4te \xB7 ${new Date().toLocaleTimeString("de-DE")}`)}catch(e){h("Verbindung fehlgeschlagen"),console.error("Ladefehler:",e)}}async function w(e,t,n){try{await p(e,t,n),setTimeout(c,500)}catch(a){console.error("Steuerfehler:",a)}}function h(e){let t=document.getElementById("headerStatus");t&&(t.textContent=e)}document.addEventListener("DOMContentLoaded",()=>{v(),c(),setInterval(c,b)});})();
//# sourceMappingURL=app.bundle.js.map
