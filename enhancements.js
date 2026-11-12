/* Peter OS — visual command interface, knowledge graph and HUD enhancements. */
(() => {
  'use strict';

  const style = document.createElement('style');
  style.textContent = `
    :root{--bg:#080c14;--panel:rgba(15,22,34,.88);--panel2:rgba(20,30,45,.84);--line:rgba(132,170,210,.16);--cyan:#83e8f4;--blue:#8ebeff;--violet:#c3b4ff;--green:#8ce2bd;--amber:#f5d69c;--muted:#91a0b5;--text:#e8f0fa;--radius:18px}
    body{background:radial-gradient(ellipse at 48% -15%,rgba(73,132,174,.22),transparent 42%),radial-gradient(ellipse at 92% 78%,rgba(120,103,183,.12),transparent 32%),#080c14!important;color:var(--text)}
    .topbar,.panel,.commandbar,.settings-card,.graph-view{background:var(--panel)!important;border-color:var(--line)!important;box-shadow:0 16px 48px rgba(0,0,0,.24),inset 0 1px rgba(255,255,255,.035)!important;backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px)}
    .topbar{border-radius:16px!important}.panel,.settings-card{border-radius:var(--radius)!important}.sidebar{background:rgba(10,15,24,.76)!important}
    .brandmark{box-shadow:0 0 24px rgba(131,232,244,.28)}.nav-btn,.btn,.filter-btn,.icon-btn,.commandbar button{border-radius:12px!important;transition:background .18s ease,transform .18s ease,border-color .18s ease!important}
    .nav-btn:hover,.btn:hover,.filter-btn:hover,.icon-btn:hover{transform:translateY(-1px);background:rgba(255,255,255,.09)!important}.nav-btn.active,.filter-btn.active{background:rgba(131,232,244,.12)!important;color:#c9f8ff!important;border-color:rgba(131,232,244,.25)!important}
    .dashboard-grid{grid-template-columns:minmax(0,1fr) minmax(340px,.96fr)!important;gap:14px!important}.side-stack{min-width:0;grid-template-rows:minmax(340px,1fr) auto auto!important}.hud-card{min-height:420px!important;display:flex;flex-direction:column}.hud-content{flex:1;min-height:320px!important;overflow:hidden;border-radius:14px;background:radial-gradient(ellipse at 50% 35%,rgba(74,114,151,.15),transparent 70%),rgba(4,9,16,.48)}
    .peter-player{width:100%!important;max-width:none!important;min-height:100%!important;gap:10px!important}.peter-player-frame{min-height:240px!important;aspect-ratio:16/9;flex:1 1 auto!important}
    .brain-status{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 10px}.brain-chip{border:1px solid rgba(255,255,255,.13);border-radius:999px;padding:6px 10px;color:#d8eaff;background:rgba(255,255,255,.055);font:10px ui-monospace,SFMono-Regular,monospace;letter-spacing:.04em}
    #view-nexus{position:relative}.nexus-overview{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:-2px 0 10px}.nexus-overview .brain-chip{background:rgba(12,21,34,.78)}
    #nexus-3d-container{background:radial-gradient(ellipse at center,rgba(115,151,194,.17),transparent 68%)!important}.graph-view{position:relative;border:1px solid var(--line)!important;box-shadow:inset 0 0 65px rgba(174,209,255,.06)!important;overflow:hidden}
    .graph-view:after{content:"PETER MEMORY FIELD · LIVE";position:absolute;top:14px;left:16px;z-index:1;pointer-events:none;color:rgba(203,223,246,.48);font:9px ui-monospace,monospace;letter-spacing:.17em}
    .graph-toolbar,.graph-bottom,.graph-legend{backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}.graph-toolbar{background:rgba(8,13,22,.58)!important;border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:8px!important}.graph-legend{background:rgba(8,13,22,.56)!important;border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:10px!important}.inspector{backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px);box-shadow:0 16px 48px rgba(0,0,0,.4)}
    .reasoning{line-height:1.6!important;color:#b9c9dc!important}.msg{line-height:1.55}.commandbar{border-radius:18px!important}.commandbar input{min-width:0}.btn.primary{box-shadow:0 5px 22px rgba(71,140,255,.2)}
    .peter-image-view{width:100%;height:100%;min-height:280px;display:grid;grid-template-rows:auto minmax(0,1fr);gap:10px;color:#f7f8fc}.peter-image-view h3{margin:0;color:#e4f2ff;font-size:14px}.peter-image-body{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(130px,.8fr);gap:14px;min-height:0;align-items:center}.peter-image-body img{width:100%;height:100%;max-height:460px;object-fit:contain;background:#090b12;border-radius:16px;border:1px solid rgba(255,255,255,.13)}.peter-image-info{font-size:11px;color:var(--muted);overflow:auto;max-height:100%}.peter-image-info a{color:#c8e5ff}
    .route-pending{opacity:.72}.route-pending:before{content:"";display:inline-block;width:7px;height:7px;margin-right:8px;border-radius:50%;background:var(--cyan);box-shadow:0 0 12px var(--cyan);animation:peterPulse 1s ease-in-out infinite alternate}@keyframes peterPulse{to{opacity:.35;transform:scale(.7)}}
    @media(max-width:1100px){.dashboard-grid{grid-template-columns:1fr!important}.side-stack{grid-template-rows:minmax(340px,1fr) auto auto!important}.hud-card{min-height:400px!important}}
    @media(max-width:760px){.dashboard-grid{grid-template-columns:1fr!important}.side-stack{display:grid;grid-template-columns:1fr!important}.hud-card{min-height:360px!important}.hud-content{min-height:280px!important}.peter-image-body{grid-template-columns:1fr;grid-template-rows:minmax(160px,1fr) auto}.peter-image-view{min-height:300px}}
    @media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;transition:none!important;scroll-behavior:auto!important}}
  `;
  document.head.appendChild(style);

  // Warm the same-origin connection before the first command; this does not add
  // a model call and keeps the existing routing/reasoning pipeline untouched.
  const warmConnection = () => fetch('/ping', { method: 'GET', cache: 'no-store' }).catch(() => {});
  if ('requestIdleCallback' in window) requestIdleCallback(warmConnection, { timeout: 1200 });
  else setTimeout(warmConnection, 300);

  const box = () => document.getElementById('hud-screen-content');
  function showImage(screen) {
    const container = box();
    if (!container || !screen?.image_url) return;
    const root = document.createElement('div'); root.className = 'peter-image-view';
    const title = document.createElement('h3'); title.textContent = screen.title || 'Immagine';
    const body = document.createElement('div'); body.className = 'peter-image-body';
    const img = document.createElement('img'); img.src = screen.image_url; img.alt = screen.title || 'Immagine trovata';
    const info = document.createElement('div'); info.className = 'peter-image-info'; info.textContent = screen.content || 'Immagine trovata sul web.';
    if (screen.source_url) {
      const link = document.createElement('a'); link.href = screen.source_url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = 'Apri fonte ↗';
      info.append(document.createElement('br'), link);
    }
    img.addEventListener('error', () => { info.textContent = 'Immagine non accessibile direttamente; prova un’altra ricerca.'; }, { once: true });
    body.append(img, info); root.append(title, body); container.replaceChildren(root);
    const badge = document.getElementById('hud-status-badge'); if (badge) badge.textContent = 'ACTIVE // IMAGE';
  }
  const originalUpdateHud = window.updateHudScreen;
  if (typeof originalUpdateHud === 'function') window.updateHudScreen = screen => {
    if (screen?.type === 'IMAGE_PREVIEW' && screen.image_url) { showImage(screen); return; }
    return originalUpdateHud(screen);
  };

  // Keep the normal /chat request as the sole reasoning pipeline. Render its
  // reply immediately, then let image lookup enhance the HUD when it completes.
  const input = document.getElementById('cmd-input');
  const send = document.getElementById('send-cmd-btn');
  let busy = false;
  const imageIntent = text => /\b(immagin(?:e|i)|foto|fotografie)\b/i.test(text) && /\b(mostra(?:mi)?|cerca|trova|fammi vedere|voglio)\b/i.test(text);
  async function sendImageRequest(event) {
    if (!input || !imageIntent(input.value.trim()) || busy) return;
    event.preventDefault(); event.stopImmediatePropagation(); busy = true;
    if (send) send.disabled = true;
    const message = input.value.trim(); input.value = '';
    const feed = document.getElementById('chat-feed');
    const append = (text, kind = 'peter') => {
      if (!feed) return;
      const el = document.createElement('div'); el.className = `msg ${kind}`; el.textContent = String(text);
      if (kind === 'user') el.classList.add('route-pending');
      feed.append(el); feed.scrollTop = feed.scrollHeight;
      return el;
    };
    append(message, 'user');
    const form = new FormData(); form.append('message', message);
    const imagePromise = fetch('/api/images/search', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: message })
    }).then(async response => ({ ok: response.ok, data: await response.json() })).catch(() => ({ ok: false, data: {} }));
    try {
      const chatResponse = await fetch('/chat', { method: 'POST', body: form });
      const chat = await chatResponse.json();
      if (!chatResponse.ok) throw new Error(chat.detail || 'Richiesta non riuscita');
      append(chat.reply || 'Risposta vuota');
      if (chat.reasoning) {
        const reasoning = document.getElementById('reasoning-preview');
        if (reasoning) reasoning.textContent = chat.reasoning;
      }
      if (chat.screen && typeof window.updateHudScreen === 'function') window.updateHudScreen(chat.screen);
      // Do not block chat/reasoning on a slower image provider.
      imagePromise.then(result => { if (result.ok && result.data?.image_url) showImage({ type: 'IMAGE_PREVIEW', ...result.data }); });
    } catch (error) {
      append(`Errore: ${error.message}`, 'system');
    } finally {
      busy = false; if (send) send.disabled = false; input.focus();
    }
  }
  if (send) send.addEventListener('click', sendImageRequest, true);
  if (input) input.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey && imageIntent(input.value.trim())) sendImageRequest(event);
  }, true);

  // Add a compact second-brain summary to the graph page without changing its
  // data model or force simulation.
  const graphView = document.getElementById('view-nexus');
  if (graphView) {
    const heading = graphView.querySelector('.view-heading');
    if (heading) {
      const overview = document.createElement('div'); overview.className = 'nexus-overview';
      for (const [label, id] of [['NODI', 'node-count'], ['LEGAMI', 'edge-count']]) {
        const chip = document.createElement('span'); chip.className = 'brain-chip';
        const value = document.getElementById(id)?.textContent || '—'; chip.textContent = `${label} · ${value}`;
        chip.dataset.source = id; overview.append(chip);
      }
      const state = document.createElement('span'); state.className = 'brain-chip'; state.id = 'peter-graph-state'; state.textContent = 'MEMORY FIELD · READY'; overview.append(state);
      heading.insertAdjacentElement('afterend', overview);
      const update = () => {
        for (const chip of overview.querySelectorAll('[data-source]')) {
          const source = document.getElementById(chip.dataset.source);
          chip.textContent = `${chip.dataset.source === 'node-count' ? 'NODI' : 'LEGAMI'} · ${source?.textContent || '—'}`;
        }
        const graphStatus = document.getElementById('graph-status');
        if (graphStatus && graphStatus.textContent) state.textContent = `MEMORY FIELD · ${graphStatus.textContent}`;
      };
      update(); setInterval(update, 1200);
    }
  }
})();
