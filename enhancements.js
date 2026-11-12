/* Peter OS — visual command interface, knowledge graph and HUD enhancements. */
(() => {
  'use strict';

  const style = document.createElement('style');
  style.textContent = `
    :root{--bg:#080c14;--panel:rgba(15,22,34,.88);--panel2:rgba(20,30,45,.84);--line:rgba(132,170,210,.16);--cyan:#83e8f4;--blue:#8ebeff;--violet:#c3b4ff;--green:#8ce2bd;--amber:#f5d69c;--muted:#91a0b7;--radius:16px}
    body{background:radial-gradient(ellipse at 48% -15%,rgba(73,132,174,.22),transparent 42%),radial-gradient(ellipse at 92% 78%,rgba(120,103,183,.12),transparent 32%),#080c14!important;color:var(--text,#e6edf7)!important}
    .topbar,.panel,.commandbar,.settings-card,.graph-view{background:var(--panel)!important;border-color:var(--line)!important;box-shadow:0 16px 48px rgba(0,0,0,.24),inset 0 1px rgba(255,255,255,.025)!important}
    .topbar{border-radius:16px!important}.panel,.settings-card{border-radius:var(--radius)!important}.sidebar{background:rgba(10,15,24,.76)!important}
    .brandmark{box-shadow:0 0 24px rgba(131,232,244,.28)}.nav-btn,.btn,.filter-btn,.icon-btn,.commandbar button{border-radius:12px!important;transition:background .18s ease,transform .18s ease,border-color .18s ease!important}
    .nav-btn:hover,.btn:hover,.filter-btn:hover,.icon-btn:hover{transform:translateY(-1px);background:rgba(255,255,255,.09)!important}.nav-btn.active,.filter-btn.active{background:rgba(131,232,244,.13)!important;border-color:rgba(131,232,244,.35)!important}
    .dashboard-grid{grid-template-columns:minmax(0,1fr) minmax(340px,.96fr)!important;gap:14px!important}.side-stack{min-width:0;grid-template-rows:minmax(340px,1fr) auto auto!important}.hud-card{min-height:400px!important}
    .peter-player{width:100%!important;max-width:none!important;min-height:100%!important;gap:10px!important}.peter-player-frame{min-height:240px!important;aspect-ratio:16/9;flex:1 1 auto!important}
    .brain-status{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 10px}.brain-chip{border:1px solid rgba(255,255,255,.13);border-radius:999px;padding:6px 10px;color:#d8eaff;background:rgba(255,255,255,.04);font:11px ui-monospace,monospace}
    #view-nexus{position:relative}.nexus-overview{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:-2px 0 10px}.nexus-overview .brain-chip{background:rgba(12,21,34,.78)}
    #nexus-3d-container{background:radial-gradient(ellipse at center,rgba(115,151,194,.17),transparent 68%)!important}.graph-view{position:relative;border:1px solid var(--line)!important;box-shadow:0 18px 55px rgba(0,0,0,.25)!important}
    .graph-view:after{content:"PETER MEMORY FIELD · LIVE";position:absolute;top:14px;left:16px;z-index:1;pointer-events:none;color:rgba(203,223,246,.48);font:9px ui-monospace,monospace;letter-spacing:.16em}
    .graph-toolbar,.graph-bottom,.graph-legend{backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}.graph-toolbar{background:rgba(8,13,22,.58)!important;border:1px solid rgba(255,255,255,.08)!important}
    .reasoning{line-height:1.6!important;color:#b9c9dc!important}.msg{line-height:1.55}.commandbar{border-radius:18px!important}.commandbar input{min-width:0}.btn.primary{box-shadow:0 5px 22px rgba(83,211,255,.18)}
    .peter-image-view{width:100%;height:100%;min-height:280px;display:grid;grid-template-rows:auto minmax(0,1fr);gap:10px;color:#f7f8fc}.peter-image-view h3{margin:0;color:#e4f2ff;font-size:14px}.peter-image-body{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(120px,.7fr);gap:12px;min-height:0}.peter-image-body img{width:100%;height:100%;min-height:220px;object-fit:contain;background:rgba(0,0,0,.22);border-radius:12px}.peter-image-info{overflow:auto;color:#b9c9dc;font-size:12px;line-height:1.6}.peter-image-info a{color:var(--cyan)}
    .route-pending{opacity:.72}.route-pending:before{content:"";display:inline-block;width:7px;height:7px;margin-right:8px;border-radius:50%;background:var(--cyan);box-shadow:0 0 12px var(--cyan);animation:peterPulse 1s infinite alternate}@keyframes peterPulse{to{opacity:.25}}
    .nexus-multi-graphs{margin:10px 0 14px}.nexus-graph-tabs{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px}.nexus-graph-tab{border:1px solid var(--line);border-radius:12px;background:rgba(14,24,38,.85);color:#d8eaff;padding:10px 14px;font:600 11px ui-monospace,monospace;letter-spacing:.05em;cursor:pointer}.nexus-graph-tab.active{background:rgba(83,211,255,.15);border-color:rgba(83,211,255,.5);color:#a8f4ff}.nexus-graph-caption{color:#aabbd0;font-size:12px;margin:0 0 9px}.nexus-graph-count{float:right;color:#9eb4cb;font:10px ui-monospace,monospace}.nexus-graph-canvas{height:min(68vh,720px);min-height:390px;border:1px solid var(--line);border-radius:16px;overflow:hidden;background:radial-gradient(ellipse at center,rgba(54,91,130,.18),rgba(4,8,15,.96) 70%)}.nexus-graph-error{padding:24px;color:#e6b5b5;font-size:13px}.graph-view.peter-legacy-hidden{display:none!important}
    @media(max-width:1100px){.dashboard-grid{grid-template-columns:1fr!important}.side-stack{grid-template-rows:minmax(340px,1fr) auto auto!important}.hud-card{min-height:400px!important}}
    @media(max-width:760px){.dashboard-grid{grid-template-columns:1fr!important}.side-stack{display:grid;grid-template-columns:1fr!important}.hud-card{min-height:360px!important}.hud-content{min-height:280px!important}.peter-image-body{grid-template-columns:1fr;grid-template-rows:minmax(180px,1fr) auto}.nexus-graph-canvas{height:65vh;min-height:360px}.nexus-graph-tab{flex:1 1 calc(50% - 8px)}}
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

  // Keep the existing Nexus graph, and offer focused 3D views backed by full-table data.
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

    const legacy = graphView.querySelector('.graph-view');
    const multi = document.createElement('section');
    multi.className = 'nexus-multi-graphs';
    multi.innerHTML = '<div class="nexus-graph-tabs" role="tablist" aria-label="Seleziona un grafo 3D"></div><p class="nexus-graph-caption"></p><div class="nexus-graph-canvas" role="region" aria-label="Grafo delle relazioni"></div>';
    if (legacy) { legacy.classList.add('peter-legacy-hidden'); legacy.insertAdjacentElement('beforebegin', multi); }
    else graphView.append(multi);
    const tabs = multi.querySelector('.nexus-graph-tabs');
    const caption = multi.querySelector('.nexus-graph-caption');
    const canvas = multi.querySelector('.nexus-graph-canvas');
    const views = [
      { id: 'family', label: 'ALBERO FAMILIARE', caption: 'Solo legami familiari espliciti: genitori e figli collegati tra loro, non tutti al centro.' },
      { id: 'people', label: 'PERSONE E RELAZIONI', caption: 'Amici e conoscenti; i collegamenti tra persone compaiono solo quando sono stati dichiarati.' },
      { id: 'chats', label: 'TUTTE LE CHAT', caption: 'Conversazioni salvate in ordine cronologico, collegate tra loro.' },
      { id: 'facts', label: 'RICORDI A LUNGO TERMINE', caption: 'Tutti i fatti salvati, separati dalle conversazioni.' },
    ];
    let graph = null;
    let activeView = null;
    let loadToken = 0;
    const color = node => node.type === 'core' ? '#32e6ac' : node.type === 'person' ? (node.relationship_group === 'family' ? '#ff6fbe' : '#478cff') : node.type === 'chat' ? '#54e8ff' : '#a687ff';
    function disposeGraph() { if (graph) { graph._destructor?.(); graph = null; } }
    async function renderView(view) {
      activeView = view.id;
      const token = ++loadToken;
      caption.textContent = view.caption;
      tabs.querySelectorAll('button').forEach(button => button.classList.toggle('active', button.dataset.view === view.id));
      canvas.replaceChildren(); disposeGraph();
      if (typeof ForceGraph3D !== 'function') { canvas.innerHTML = '<div class="nexus-graph-error">Libreria 3D non disponibile. Ricarica la pagina per riprovare.</div>'; return; }
      canvas.innerHTML = '<div class="nexus-graph-error">Caricamento del grafo…</div>';
      try {
        const response = await fetch(`/api/nexus/${view.id}`, { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (token !== loadToken || activeView !== view.id) return;
        const nodes = Array.isArray(data.nodes) ? data.nodes : [];
        const nodeIds = new Set(nodes.map(node => String(node.id)));
        const links = (Array.isArray(data.edges) ? data.edges : []).filter(edge => nodeIds.has(String(edge.source?.id ?? edge.source)) && nodeIds.has(String(edge.target?.id ?? edge.target))).map(edge => ({ ...edge, source: String(edge.source?.id ?? edge.source), target: String(edge.target?.id ?? edge.target), relation: edge.relation_type || edge.category || '' }));
        caption.innerHTML = `${view.caption}<span class="nexus-graph-count">${nodes.length} NODI · ${links.length} LEGAMI</span>`;
        canvas.replaceChildren();
        if (!nodes.length) { canvas.innerHTML = '<div class="nexus-graph-error">Non ci sono ancora dati salvati per questa vista.</div>'; return; }
        graph = ForceGraph3D()(canvas)
          .backgroundColor('rgba(3,7,13,0)')
          .graphData({ nodes, links })
          .nodeId('id')
          .nodeLabel(node => `${node.name || node.id}${node.relation_type ? ` · ${node.relation_type}` : ''}`)
          .nodeColor(color)
          .nodeVal(node => node.type === 'core' ? 12 : view.id === 'chats' ? 4 : 7)
          .linkColor(link => String(link.category || '').includes('famiglia') ? '#32e6ac' : view.id === 'chats' ? '#54e8ff' : '#8298b4')
          .linkOpacity(.62)
          .linkDirectionalParticles(2)
          .linkDirectionalParticleWidth(2)
          .linkDirectionalParticleColor(link => String(link.category || '').includes('famiglia') ? '#32e6ac' : '#83e8f4')
          .onNodeClick(node => {
            const inspector = document.getElementById('nexus-inspector');
            const title = document.getElementById('inspector-title');
            const meta = document.getElementById('inspector-meta');
            const type = document.getElementById('inspector-type');
            if (title) title.textContent = node.name || node.id;
            if (meta) meta.textContent = node.notes || node.relation_type || node.created_at || '';
            if (type) type.textContent = `NODE // ${(node.type || 'unknown').toUpperCase()}`;
            if (inspector) inspector.classList.add('open');
          });
        graph.d3Force('charge')?.strength(-160);
        graph.d3Force('link')?.distance(view.id === 'family' ? 100 : 75);
        setTimeout(() => { if (token === loadToken) graph?.zoomToFit(500, 60); }, 250);
      } catch (error) {
        if (token === loadToken) canvas.innerHTML = `<div class="nexus-graph-error">Impossibile caricare il grafo: ${String(error.message || error)}</div>`;
      }
    }
    for (const view of views) {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'nexus-graph-tab'; button.dataset.view = view.id;
      button.setAttribute('role', 'tab'); button.textContent = view.label;
      button.addEventListener('click', () => renderView(view));
      tabs.append(button);
    }
    const resizeObserver = new ResizeObserver(() => graph?.width(canvas.clientWidth).height(canvas.clientHeight));
    resizeObserver.observe(canvas);
    const refresh = document.getElementById('graph-refresh');
    refresh?.addEventListener('click', () => { if (activeView) renderView(views.find(view => view.id === activeView)); });
    const nexusNav = document.querySelector('.nav-btn[data-view="nexus"]');
    nexusNav?.addEventListener('click', () => { if (!activeView) renderView(views[0]); }, { once: true });
    if (graphView.classList.contains('active')) renderView(views[0]);
    window.addEventListener('beforeunload', () => { resizeObserver.disconnect(); disposeGraph(); }, { once: true });
  }
})();
