(()=>{async function M(){let t=await fetch("api/devices");if(!t.ok)throw new Error(`HTTP ${t.status}`);return t.json()}async function T(t,e,s){let r=await fetch("api/control",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({device_id:t,action:e,value:s})});if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json()}function $(t){let e=t.state==="ON",s=t.brightness??0,r=t.protocol==="z2m"?254:100,o=Math.round(s/r*100),a=e?"light-on":"",n=e?1:.3;return`
    <div class="light-card ${a}">
      <div class="light-bulb" data-action="power" data-id="${t.id}" data-state="${e?"ON":"OFF"}">
        <svg style="width:48px;height:48px;opacity:${n}" viewBox="0 0 24 24" fill="none" stroke="${e?"#fbbf24":"var(--text-muted)"}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 18h6M10 22h4"/>
          <path d="M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z" fill="${e?"rgba(251,191,36,.15)":"none"}"/>
        </svg>
      </div>
      <div class="light-info">
        <span class="light-pct">${o}%</span>
      </div>
      <input type="range" class="light-slider" min="0" max="${r}" value="${s}" data-action="brightness" data-id="${t.id}" data-max="${r}">
    </div>`}function C(t){document.querySelectorAll(".light-bulb").forEach(e=>{e.addEventListener("click",()=>{let r=e.dataset.state==="ON"?"OFF":"ON";e.dataset.state=r;let o=e.closest(".device-card"),a=o?.querySelector(".light-card"),n=o?.querySelector(".light-pct");r==="ON"?a?.classList.add("light-on"):(a?.classList.remove("light-on"),n&&(n.textContent="Aus")),t(e.dataset.id,"power",r)})}),document.querySelectorAll(".light-slider").forEach(e=>{let s;e.addEventListener("input",()=>{let o=e.closest(".device-card")?.querySelector(".light-pct"),a=Number(e.dataset.max||100),n=Math.round(e.value/a*100);o&&(o.textContent=`${n}%`)}),e.addEventListener("change",()=>{clearTimeout(s),s=setTimeout(()=>{t(e.dataset.id,"brightness",Number(e.value))},300)})})}var Y=[{value:"off",label:"Aus"},{value:"heat",label:"Heizen"},{value:"auto",label:"Auto"}];function w(t){let e=t.temperature??20,s=t.current_temp,r=t.system_mode||"off",o=t.heating==="ON"||r==="heat",a=t.last_seen!=null||t.temperature!=null,n=o?"Heizt...":"Standby",c=o?"heating":"idle",d=a?"":"offline",u=a?"Online":"Offline",h=s!=null?`Ist-Temperatur: ${s}\xB0C`:"",p=Y.map(m=>`<button class="thermo-mode-btn ${m.value===r?"active":""}" data-mode="${m.value}" data-id="${t.id}">${m.label}</button>`).join("");return`
    <div class="thermo-card">
      <div class="thermo-header">
        <span class="thermo-state"><span class="dot ${c}"></span>${n}</span>
        <span class="thermo-badge ${d}">${u}</span>
      </div>
      <div class="thermo-setpoint">${e}\xB0C</div>
      <div class="thermo-current">${h}</div>
      <input type="range" class="thermo-slider" min="5" max="30" step="0.5" value="${e}" data-action="temperature" data-id="${t.id}">
      <div class="thermo-modes">${p}</div>
    </div>`}function A(t){document.querySelectorAll(".thermo-slider").forEach(e=>{let s;e.addEventListener("input",()=>{let o=e.closest(".device-card")?.querySelector(".thermo-setpoint");o&&(o.textContent=`${e.value}\xB0C`)}),e.addEventListener("change",()=>{clearTimeout(s),s=setTimeout(()=>{t(e.dataset.id,"temperature",Number(e.value))},400)})}),document.querySelectorAll(".thermo-mode-btn").forEach(e=>{e.addEventListener("click",()=>{e.closest(".thermo-modes").querySelectorAll(".thermo-mode-btn").forEach(r=>r.classList.remove("active")),e.classList.add("active"),t(e.dataset.id,"system_mode",e.dataset.mode)})})}function O(t){return t?Date.now()-new Date(t).getTime()>864e5:!1}var q=0,R=40;function b(t){let e=t.temperature??null,s=t.unit||"\xB0C",o=O(t.last_seen)?"status-dot stale":"status-dot live";if(e===null)return`<div class="sensor-gauge">
      <span class="${o}"></span>
      <div class="gauge-value">\u2013${s}</div>
    </div>`;if(s!=="\xB0C")return G(e,s,o);let a=Math.max(0,Math.min(100,(e-q)/(R-q)*100)),n=52,c=2*Math.PI*n,d=c-a/100*c,u="#06d6a0";return e>30?u="var(--red)":e<10&&(u="#48bfe3"),`
    <div class="sensor-gauge">
      <span class="${o}"></span>
      <svg class="gauge-ring" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="${n}" fill="none" stroke="var(--border)" stroke-width="8"/>
        <circle cx="60" cy="60" r="${n}" fill="none" stroke="${u}" stroke-width="8"
                stroke-dasharray="${c}" stroke-dashoffset="${d}"
                stroke-linecap="round" transform="rotate(-90 60 60)"/>
      </svg>
      <div class="gauge-value">${e}${s}</div>
    </div>`}function G(t,e,s){let r=Number(t).toFixed(2),[o,a]=r.split("."),c=o.padStart(5,"0").split("").map(d=>`<span class="counter-digit">${d}</span>`).join("")+'<span class="counter-sep">.</span>'+a.split("").map(d=>`<span class="counter-digit counter-decimal">${d}</span>`).join("");return`
    <div class="counter-display">
      <span class="${s}"></span>
      <div class="counter-digits">${c}</div>
      <div class="counter-unit">${e}</div>
    </div>`}function D(t){let e=t.position??100,s=18+Math.round((100-e)*1.02),r="width:22px;height:22px;stroke:currentColor;stroke-width:2.5;fill:none;stroke-linecap:round;stroke-linejoin:round;display:block",o=`
    <svg viewBox="0 0 160 140" style="width:100%;height:140px;display:block;touch-action:none">
      <rect x="20" y="14" width="120" height="120" rx="3" fill="none" stroke="var(--border)" stroke-width="2"/>
      <line x1="80" y1="14" x2="80" y2="134" stroke="var(--border)" stroke-width="1.5"/>
      <rect x="132" y="62" width="4" height="16" rx="1" fill="none" stroke="var(--text-muted)" stroke-width="1.5"/>
      <rect x="18" y="10" width="124" height="10" rx="5" fill="var(--text-muted)" opacity=".4"/>
      <rect class="roller-cloth" x="22" y="18" width="116" height="${s-18}" rx="1" fill="var(--text-muted)" opacity=".4"/>
      <rect class="roller-bar" x="22" y="${s-4}" width="116" height="5" rx="2" fill="var(--text-muted)" opacity=".6"/>
      <line x1="80" y1="${s+4}" x2="80" y2="134" stroke="var(--text-muted)" stroke-width="1" opacity=".4"/>
      <circle class="roller-handle" cx="80" cy="${s+4}" r="6" fill="var(--accent)" opacity=".8"/>
    </svg>`;return`
    <div class="roller-visual">
      <div class="roller-buttons-col">
        <span class="btn-roller" data-action="roller_cmd" data-id="${t.id}" data-value="open" title="Auf"><svg style="${r}" viewBox="0 0 24 24"><path d="M12 19V5M5 12l7-7 7 7"/></svg></span>
        <span class="btn-roller" data-action="roller_cmd" data-id="${t.id}" data-value="stop" title="Stop"><svg style="${r}" viewBox="0 0 24 24"><rect x="7" y="7" width="10" height="10" rx="1"/></svg></span>
        <span class="btn-roller" data-action="roller_cmd" data-id="${t.id}" data-value="close" title="Zu"><svg style="${r}" viewBox="0 0 24 24"><path d="M12 5v14M5 12l7 7 7-7"/></svg></span>
      </div>
      <div class="roller-window-wrap">
        ${o}
        <div class="roller-pos-badge">${e}%</div>
      </div>
    </div>
    `}var g=t=>`<svg style="width:16px;height:16px;vertical-align:-2px;stroke:currentColor;stroke-width:2;fill:none;display:inline" viewBox="0 0 24 24">${t}</svg>`,E={switch:g('<path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/>'),dimmer:g('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>'),roller:g('<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18"/>'),thermostat:g('<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>'),sensor:g('<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/><path d="M10 13V4"/>')};function N(t){document.querySelectorAll(".roller-window-wrap").forEach(e=>{let s=e.querySelector("svg"),r=e.closest(".device-card");if(!s||!r)return;let o=r.dataset.id,a=s.querySelector(".roller-cloth"),n=s.querySelector(".roller-bar"),c=s.querySelector(".roller-handle"),d=e.querySelector(".roller-pos-badge");if(!a||!c)return;let u=!1,h=18,p=120;function m(i){let l=Math.max(h,Math.min(p,i));return Math.round(100-(l-h)/(p-h)*100)}function Q(i){return h+(100-i)/100*(p-h)}function z(i){let l=i-h;a.setAttribute("height",l),n&&n.setAttribute("y",i-4),c.setAttribute("cy",i+4);let v=m(i);d&&(d.textContent=`${v}%`)}function S(i){let l=s.createSVGPoint(),v=i.touches?i.touches[0]:i;return l.x=v.clientX,l.y=v.clientY,l.matrixTransform(s.getScreenCTM().inverse()).y}c.style.cursor="ns-resize",a.style.cursor="ns-resize";function f(i){i.preventDefault(),u=!0,e.classList.add("dragging")}function k(i){if(!u)return;i.preventDefault();let l=S(i);z(l)}function L(i){if(!u)return;u=!1,e.classList.remove("dragging");let l=S(i.changedTouches?i.changedTouches[0]:i),v=m(l);t(o,"position",v)}c.addEventListener("mousedown",f),a.addEventListener("mousedown",f),document.addEventListener("mousemove",k),document.addEventListener("mouseup",L),c.addEventListener("touchstart",f,{passive:!1}),a.addEventListener("touchstart",f,{passive:!1}),document.addEventListener("touchmove",k,{passive:!1}),document.addEventListener("touchend",L)})}function _(t){let e=t.state==="ON";return`
    <div class="switch-card ${e?"switch-on":""}">
      <div class="switch-btn" data-action="power" data-id="${t.id}" data-state="${t.state||"OFF"}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M12 2v6"/>
          <circle cx="12" cy="14" r="8"/>
        </svg>
      </div>
      <span class="switch-label">${e?"Ein":"Aus"}</span>
    </div>`}function B(t){document.querySelectorAll(".switch-btn").forEach(e=>{e.addEventListener("click",()=>{let r=e.dataset.state==="ON"?"OFF":"ON";e.dataset.state=r;let o=e.closest(".device-card"),a=o?.querySelector(".switch-card"),n=o?.querySelector(".switch-label");r==="ON"?(a?.classList.add("switch-on"),n&&(n.textContent="Ein")):(a?.classList.remove("switch-on"),n&&(n.textContent="Aus")),t(e.dataset.id,"power",r)})})}var x=null;function F(t,e){x=e;let s=document.getElementById("deviceGrid");if(!s)return;let r={},o={roller:"Rolll\xE4den",sensor:"Temperatursensoren",thermostat:"Heizungsthermostate",dimmer:"Lichter",light:"Lichter",switch:"Schalter"};for(let n of t){let c=o[n.type]||n.type;r[c]||(r[c]=[]),r[c].push(n)}let a="";for(let[n,c]of Object.entries(r))a+=`<div class="device-group">
      <h2 class="group-title">${n}</h2>
      <div class="device-grid-inner">${c.map(d=>H(d)).join("")}</div>
    </div>`;s.innerHTML=a,X(),N(e),A(e),C(e),B(e)}function H(t){let e=E[t.type]||E.switch,s=Z(t);return`
    <div class="device-card" data-id="${t.id}" data-type="${t.type}">
      <div class="device-card-header">
        <div>
          <div class="device-name">${e} ${t.name}</div>
          <div class="device-type">${t.id}</div>
        </div>
        
      </div>
      ${s}
      <div class="device-status">${t.status||""}</div>
    </div>`}function Z(t){switch(t.type){case"dimmer":case"light":return $(t);case"roller":return D(t);case"thermostat":return w(t);case"sensor":return b(t);case"switch":return _(t);default:return""}}function X(){document.querySelectorAll('[data-action="power"]').forEach(t=>{t.addEventListener("change",()=>{x(t.dataset.id,"power",t.checked?"ON":"OFF")})}),document.querySelectorAll('[data-action="roller_cmd"]').forEach(t=>{t.addEventListener("click",()=>{t.classList.add("active"),setTimeout(()=>t.classList.remove("active"),1500),x(t.dataset.id,"roller_cmd",t.dataset.value)})}),document.querySelectorAll('input[type="range"]').forEach(t=>{let e;t.addEventListener("input",()=>{let s=t.closest(".slider-control")?.querySelector(".slider-label span:last-child"),r=t.closest(".device-card")?.querySelector(".roller-pos-badge"),o=t.dataset.action==="temperature"?"\xB0C":"%";s&&(s.textContent=`${t.value}${o}`),r&&(r.textContent=`${t.value}%`)}),t.addEventListener("change",()=>{clearTimeout(e),e=setTimeout(()=>{x(t.dataset.id,t.dataset.action,Number(t.value))},300)})})}var j="alexa-theme";function P(){let t=localStorage.getItem(j)||"dark";document.documentElement.setAttribute("data-theme",t);let e=document.getElementById("themeToggle");e&&e.addEventListener("click",()=>{let s=document.documentElement.getAttribute("data-theme")==="dark"?"light":"dark";document.documentElement.setAttribute("data-theme",s),localStorage.setItem(j,s)})}var J=3e4,y=[];async function I(){try{y=await M(),F(y,K),V(`${y.length} Ger\xE4te \xB7 ${new Date().toLocaleTimeString("de-DE")}`)}catch(t){V("Verbindung fehlgeschlagen"),console.error("Ladefehler:",t)}}async function K(t,e,s){try{await T(t,e,s);let r=y.find(o=>o.id===t);r&&(e==="power"&&(r.state=s),e==="brightness"&&(r.brightness=s),e==="position"&&(r.position=s),e==="temperature"&&(r.temperature=s),e==="system_mode"&&(r.system_mode=s))}catch(r){console.error("Steuerfehler:",r)}}function V(t){let e=document.getElementById("headerStatus");e&&(e.textContent=t)}document.addEventListener("DOMContentLoaded",()=>{P(),I(),setInterval(I,J)});})();
//# sourceMappingURL=app.bundle.js.map
