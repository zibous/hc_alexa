(()=>{async function C(){let t=await fetch("api/devices");if(!t.ok)throw new Error(`HTTP ${t.status}`);return t.json()}async function O(t,e,r){let s=await fetch("api/control",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({device_id:t,action:e,value:r})});if(!s.ok)throw new Error(`HTTP ${s.status}`);return s.json()}function b(t){let e=t.state==="ON",r=t.brightness??0,s=t.protocol==="z2m"?254:100,o=Math.round(r/s*100),a=e?"light-on":"",i=e?1:.3;return`
    <div class="light-card ${a}">
      <div class="light-bulb" data-action="power" data-id="${t.id}" data-state="${e?"ON":"OFF"}">
        <svg style="width:48px;height:48px;opacity:${i}" viewBox="0 0 24 24" fill="none" stroke="${e?"#fbbf24":"var(--text-muted)"}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 18h6M10 22h4"/>
          <path d="M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z" fill="${e?"rgba(251,191,36,.15)":"none"}"/>
        </svg>
      </div>
      <div class="light-info">
        <span class="light-pct">${o}%</span>
      </div>
      <input type="range" class="light-slider" min="0" max="${s}" value="${r}" data-action="brightness" data-id="${t.id}" data-max="${s}">
    </div>`}function T(t){document.querySelectorAll(".light-bulb").forEach(e=>{e.addEventListener("click",()=>{let s=e.dataset.state==="ON"?"OFF":"ON";e.dataset.state=s;let o=e.closest(".device-card"),a=o?.querySelector(".light-card"),i=o?.querySelector(".light-pct");s==="ON"?a?.classList.add("light-on"):(a?.classList.remove("light-on"),i&&(i.textContent="Aus")),t(e.dataset.id,"power",s)})}),document.querySelectorAll(".light-slider").forEach(e=>{let r;e.addEventListener("input",()=>{let o=e.closest(".device-card")?.querySelector(".light-pct"),a=Number(e.dataset.max||100),i=Math.round(e.value/a*100);o&&(o.textContent=`${i}%`)}),e.addEventListener("change",()=>{clearTimeout(r),r=setTimeout(()=>{t(e.dataset.id,"brightness",Number(e.value))},300)})})}var H=[{value:"off",label:"Aus"},{value:"heat",label:"Heizen"},{value:"auto",label:"Auto"}],Z=[{value:"off",label:"Aus"},{value:"cool",label:"K\xFChlen"},{value:"auto",label:"Auto"}];function w(t){let e=t.temperature??20,r=t.current_temp,s=t.system_mode||"off",o=t.protocol==="midea",a=o?s!=="off"&&t.state==="ON":t.heating==="ON"||s==="heat",i=t.last_seen!=null||t.temperature!=null,n=o?a?s==="cool"?"K\xFChlt...":s==="heat"?"Heizt...":"Aktiv":"Standby":a?"Heizt...":"Standby",l=a?"heating":"idle",d=i?"":"offline",h=i?"Online":"Offline",v=r!=null?`Ist-Temperatur: ${r}\xB0C`:"",k=(o?Z:H).map(g=>`<button class="thermo-mode-btn ${g.value===s?"active":""}" data-mode="${g.value}" data-id="${t.id}">${g.label}</button>`).join("");return`
    <div class="thermo-card">
      <div class="thermo-header">
        <span class="thermo-state"><span class="dot ${l}"></span>${n}</span>
        <span class="thermo-badge ${d}">${h}</span>
      </div>
      <div class="thermo-setpoint">${e}\xB0C</div>
      <div class="thermo-current">${v}</div>
      <input type="range" class="thermo-slider" min="${o?16:5}" max="30" step="${o?1:.5}" value="${e}" data-action="temperature" data-id="${t.id}">
      <div class="thermo-modes">${k}</div>
    </div>`}function q(t){document.querySelectorAll(".thermo-slider").forEach(e=>{let r;e.addEventListener("input",()=>{let o=e.closest(".device-card")?.querySelector(".thermo-setpoint");o&&(o.textContent=`${e.value}\xB0C`)}),e.addEventListener("change",()=>{clearTimeout(r),r=setTimeout(()=>{t(e.dataset.id,"temperature",Number(e.value))},1500)})}),document.querySelectorAll(".thermo-mode-btn").forEach(e=>{e.addEventListener("click",()=>{e.closest(".thermo-modes").querySelectorAll(".thermo-mode-btn").forEach(s=>s.classList.remove("active")),e.classList.add("active"),t(e.dataset.id,"system_mode",e.dataset.mode)})})}function N(t){return t?Date.now()-new Date(t).getTime()>864e5:!1}var _=0,K=40;function E(t){let e=t.temperature??null,r=t.unit||"\xB0C",o=N(t.last_seen)?"status-dot stale":"status-dot live";if(e===null)return`<div class="sensor-gauge">
      <span class="${o}"></span>
      <div class="gauge-value">\u2013${r}</div>
    </div>`;if(r!=="\xB0C")return X(e,r,o);let a=Math.max(0,Math.min(100,(e-_)/(K-_)*100)),i=52,n=2*Math.PI*i,l=n-a/100*n,d="#06d6a0";return e>30?d="var(--red)":e<10&&(d="#48bfe3"),`
    <div class="sensor-gauge">
      <span class="${o}"></span>
      <svg class="gauge-ring" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="${i}" fill="none" stroke="var(--border)" stroke-width="8"/>
        <circle cx="60" cy="60" r="${i}" fill="none" stroke="${d}" stroke-width="8"
                stroke-dasharray="${n}" stroke-dashoffset="${l}"
                stroke-linecap="round" transform="rotate(-90 60 60)"/>
      </svg>
      <div class="gauge-value">${e}${r}</div>
    </div>`}function X(t,e,r){let s=Number(t).toFixed(2),[o,a]=s.split("."),n=o.padStart(5,"0").split("").map(l=>`<span class="counter-digit">${l}</span>`).join("")+'<span class="counter-sep">.</span>'+a.split("").map(l=>`<span class="counter-digit counter-decimal">${l}</span>`).join("");return`
    <div class="counter-display">
      <span class="${r}"></span>
      <div class="counter-digits">${n}</div>
      <div class="counter-unit">${e}</div>
    </div>`}function D(t){let e=t.position??100,r=18+Math.round((100-e)*1.02),s="width:22px;height:22px;stroke:currentColor;stroke-width:2.5;fill:none;stroke-linecap:round;stroke-linejoin:round;display:block",o=`
    <svg viewBox="0 0 160 140" style="width:100%;height:140px;display:block;touch-action:none">
      <rect x="20" y="14" width="120" height="120" rx="3" fill="none" stroke="var(--border)" stroke-width="2"/>
      <line x1="80" y1="14" x2="80" y2="134" stroke="var(--border)" stroke-width="1.5"/>
      <rect x="132" y="62" width="4" height="16" rx="1" fill="none" stroke="var(--text-muted)" stroke-width="1.5"/>
      <rect x="18" y="10" width="124" height="10" rx="5" fill="var(--text-muted)" opacity=".4"/>
      <rect class="roller-cloth" x="22" y="18" width="116" height="${r-18}" rx="1" fill="var(--text-muted)" opacity=".4"/>
      <rect class="roller-bar" x="22" y="${r-4}" width="116" height="5" rx="2" fill="var(--text-muted)" opacity=".6"/>
      <line x1="80" y1="${r+4}" x2="80" y2="134" stroke="var(--text-muted)" stroke-width="1" opacity=".4"/>
      <circle class="roller-handle" cx="80" cy="${r+4}" r="6" fill="var(--accent)" opacity=".8"/>
    </svg>`;return`
    <div class="roller-visual">
      <div class="roller-buttons-col">
        <span class="btn-roller" data-action="roller_cmd" data-id="${t.id}" data-value="open" title="Auf"><svg style="${s}" viewBox="0 0 24 24"><path d="M12 19V5M5 12l7-7 7 7"/></svg></span>
        <span class="btn-roller" data-action="roller_cmd" data-id="${t.id}" data-value="stop" title="Stop"><svg style="${s}" viewBox="0 0 24 24"><rect x="7" y="7" width="10" height="10" rx="1"/></svg></span>
        <span class="btn-roller" data-action="roller_cmd" data-id="${t.id}" data-value="close" title="Zu"><svg style="${s}" viewBox="0 0 24 24"><path d="M12 5v14M5 12l7 7 7-7"/></svg></span>
      </div>
      <div class="roller-window-wrap">
        ${o}
        <div class="roller-pos-badge">${e}%</div>
      </div>
    </div>
    `}var f=t=>`<svg style="width:16px;height:16px;vertical-align:-2px;stroke:currentColor;stroke-width:2;fill:none;display:inline" viewBox="0 0 24 24">${t}</svg>`,S={switch:f('<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>'),dimmer:f('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>'),roller:f('<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18"/>'),thermostat:f('<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>'),sensor:f('<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/><path d="M10 13V4"/>'),purifier:f('<path d="M8 2h8l2 4H6l2-4Z"/><rect x="6" y="6" width="12" height="14" rx="2"/><circle cx="12" cy="13" r="3"/><path d="M12 10v-1M9.5 11.5l-.7-.7M14.5 11.5l.7-.7"/>')};function B(t){document.querySelectorAll(".roller-window-wrap").forEach(e=>{let r=e.querySelector("svg"),s=e.closest(".device-card");if(!r||!s)return;let o=s.dataset.id,a=r.querySelector(".roller-cloth"),i=r.querySelector(".roller-bar"),n=r.querySelector(".roller-handle"),l=e.querySelector(".roller-pos-badge");if(!a||!n)return;let d=!1,h=18,v=120;function p(c){let u=Math.max(h,Math.min(v,c));return Math.round(100-(u-h)/(v-h)*100)}function k(c){return h+(100-c)/100*(v-h)}function g(c){let u=c-h;a.setAttribute("height",u),i&&i.setAttribute("y",c-4),n.setAttribute("cy",c+4);let m=p(c);l&&(l.textContent=`${m}%`)}function L(c){let u=r.createSVGPoint(),m=c.touches?c.touches[0]:c;return u.x=m.clientX,u.y=m.clientY,u.matrixTransform(r.getScreenCTM().inverse()).y}n.style.cursor="ns-resize",a.style.cursor="ns-resize";function x(c){c.preventDefault(),d=!0,e.classList.add("dragging")}function M(c){if(!d)return;c.preventDefault();let u=L(c);g(u)}function A(c){if(!d)return;d=!1,e.classList.remove("dragging");let u=L(c.changedTouches?c.changedTouches[0]:c),m=p(u);t(o,"position",m)}n.addEventListener("mousedown",x),a.addEventListener("mousedown",x),document.addEventListener("mousemove",M),document.addEventListener("mouseup",A),n.addEventListener("touchstart",x,{passive:!1}),a.addEventListener("touchstart",x,{passive:!1}),document.addEventListener("touchmove",M,{passive:!1}),document.addEventListener("touchend",A)})}function F(t){let e=t.state==="ON";return`
    <div class="switch-card ${e?"switch-on":""}">
      <div class="switch-btn" data-action="power" data-id="${t.id}" data-state="${t.state||"OFF"}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M12 2v6"/>
          <circle cx="12" cy="14" r="8"/>
        </svg>
      </div>
      <span class="switch-label">${e?"Ein":"Aus"}</span>
    </div>`}function P(t){document.querySelectorAll(".switch-btn").forEach(e=>{e.addEventListener("click",()=>{let s=e.dataset.state==="ON"?"OFF":"ON";e.dataset.state=s;let o=e.closest(".device-card"),a=o?.querySelector(".switch-card"),i=o?.querySelector(".switch-label");s==="ON"?(a?.classList.add("switch-on"),i&&(i.textContent="Ein")):(a?.classList.remove("switch-on"),i&&(i.textContent="Aus")),t(e.dataset.id,"power",s)})})}var J=[{value:"Auto",label:"Auto"},{value:"Silent",label:"Leise"},{value:"Favorite",label:"Turbo"}];function I(t){let e=t.state==="ON",r=t.mode||"unknown",s=t.aqi,o=t.state!=null,a="\u2013",i="aqi-unknown";s!=null&&(s<=12?(a="Sehr gut",i="aqi-good"):s<=35?(a="Gut",i="aqi-moderate"):s<=55?(a="M\xE4\xDFig",i="aqi-unhealthy-sensitive"):s<=150?(a="Schlecht",i="aqi-unhealthy"):(a="Sehr schlecht",i="aqi-hazardous"));let n=o?"":"offline",l=o?"Online":"Offline",d=r.includes(".")?r.split(".").pop():r,h=J.map(p=>`<button class="purifier-mode-btn ${p.value===d?"active":""}" data-mode="${p.value}" data-id="${t.id}">${p.label}</button>`).join("");return`
    <div class="purifier-card ${e?"purifier-on":""}">
      <div class="purifier-header">
        <span class="purifier-state">
          <span class="dot ${e?"heating":"idle"}"></span>
          ${e?"Aktiv":"Aus"}
        </span>
        <span class="thermo-badge ${n}">${l}</span>
      </div>
      <div class="purifier-aqi ${i}">
        <span class="purifier-aqi-value">${s??"\u2013"}</span>
        <span class="purifier-aqi-unit">\xB5g/m\xB3</span>
        <span class="purifier-aqi-label">${a}</span>
      </div>
      <div class="purifier-power">
        <div class="switch-btn purifier-power-btn" data-action="power" data-id="${t.id}" data-state="${t.state||"OFF"}">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M12 2v6"/>
            <circle cx="12" cy="14" r="8"/>
          </svg>
        </div>
      </div>
      <div class="purifier-modes">${h}</div>
    </div>`}function j(t){document.querySelectorAll(".purifier-power-btn").forEach(e=>{e.addEventListener("click",()=>{let s=e.dataset.state==="ON"?"OFF":"ON";e.dataset.state=s;let o=e.closest(".purifier-card");s==="ON"?o?.classList.add("purifier-on"):o?.classList.remove("purifier-on"),t(e.dataset.id,"power",s)})}),document.querySelectorAll(".purifier-mode-btn").forEach(e=>{e.addEventListener("click",()=>{e.closest(".purifier-modes").querySelectorAll(".purifier-mode-btn").forEach(s=>s.classList.remove("active")),e.classList.add("active"),t(e.dataset.id,"purifier_mode",e.dataset.mode)})})}var y=null;function z(t,e){y=e;let r=document.getElementById("deviceGrid");if(!r)return;let s={},o={roller:"Rolll\xE4den",sensor:"Temperatursensoren",thermostat:"Heizungsthermostate",dimmer:"Lichter",light:"Lichter",switch:"Schalter",purifier:"Luftreiniger"};for(let i of t){let n=o[i.type]||i.type;s[n]||(s[n]=[]),s[n].push(i)}let a="";for(let[i,n]of Object.entries(s))a+=`<div class="device-group">
      <h2 class="group-title">${i}</h2>
      <div class="device-grid-inner">${n.map(l=>U(l)).join("")}</div>
    </div>`;r.innerHTML=a,W(),B(e),q(e),T(e),P(e),j(e)}function U(t){let e=S[t.type]||S.switch,r=Q(t);return`
    <div class="device-card" data-id="${t.id}" data-type="${t.type}">
      <div class="device-card-header">
        <div>
          <div class="device-name">${e} ${t.name}</div>
          <div class="device-type">${t.id}</div>
        </div>
        
      </div>
      ${r}
      <div class="device-status">${t.status||""}</div>
    </div>`}function Q(t){switch(t.type){case"dimmer":case"light":return b(t);case"roller":return D(t);case"thermostat":return w(t);case"sensor":return E(t);case"switch":return F(t);case"purifier":return I(t);default:return""}}function W(){document.querySelectorAll('[data-action="power"]').forEach(t=>{t.addEventListener("change",()=>{y(t.dataset.id,"power",t.checked?"ON":"OFF")})}),document.querySelectorAll('[data-action="roller_cmd"]').forEach(t=>{t.addEventListener("click",()=>{t.classList.add("active"),setTimeout(()=>t.classList.remove("active"),1500),y(t.dataset.id,"roller_cmd",t.dataset.value)})}),document.querySelectorAll('input[type="range"]').forEach(t=>{let e;t.addEventListener("input",()=>{let r=t.closest(".slider-control")?.querySelector(".slider-label span:last-child"),s=t.closest(".device-card")?.querySelector(".roller-pos-badge"),o=t.dataset.action==="temperature"?"\xB0C":"%";r&&(r.textContent=`${t.value}${o}`),s&&(s.textContent=`${t.value}%`)}),t.addEventListener("change",()=>{clearTimeout(e),e=setTimeout(()=>{y(t.dataset.id,t.dataset.action,Number(t.value))},300)})})}var V="alexa-theme";function R(){let t=localStorage.getItem(V)||"dark";document.documentElement.setAttribute("data-theme",t);let e=document.getElementById("themeToggle");e&&e.addEventListener("click",()=>{let r=document.documentElement.getAttribute("data-theme")==="dark"?"light":"dark";document.documentElement.setAttribute("data-theme",r),localStorage.setItem(V,r)})}var tt=3e4,$=[];async function Y(){try{$=await C(),z($,et),G(`${$.length} Ger\xE4te \xB7 ${new Date().toLocaleTimeString("de-DE")}`)}catch(t){G("Verbindung fehlgeschlagen"),console.error("Ladefehler:",t)}}async function et(t,e,r){try{await O(t,e,r);let s=$.find(o=>o.id===t);s&&(e==="power"&&(s.state=r),e==="brightness"&&(s.brightness=r),e==="position"&&(s.position=r),e==="temperature"&&(s.temperature=r),e==="system_mode"&&(s.system_mode=r))}catch(s){console.error("Steuerfehler:",s)}}function G(t){let e=document.getElementById("headerStatus");e&&(e.textContent=t)}document.addEventListener("DOMContentLoaded",()=>{R(),Y(),setInterval(Y,tt)});})();
//# sourceMappingURL=app.bundle.js.map
