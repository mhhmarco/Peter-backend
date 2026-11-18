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
    .dashboard-grid{grid-template-columns:minmax(0,1.08fr) minmax(320px,.92fr)!important;gap:14px!important}.side-stack{min-width:0;display:flex!important;flex-direction:column!important;gap:14px!important}.hud-card{min-height:360px!important;display:flex!important;flex-direction:column!important}.hud-content{flex:1 1 auto!important;min-height:280px!important;display:flex!important;flex-direction:column!important;overflow:hidden!important}
    .peter-player{width:100%!important;max-width:none!important;min-height:100%!important;gap:10px!important}.peter-player-frame{min-height:220px!important;aspect-ratio:16/9;flex:1 1 auto!important}
    .brain-status{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 10px}.brain-chip{border:1px solid rgba(255,255,255,.13);border-radius:999px;padding:6px 10px;color:#d8eaff;background:rgba(255,255,255,.04);font:11px ui-monospace,monospace}
    #view-nexus{position:relative}.nexus-overview{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:-2px 0 10px}.nexus-overview .brain-chip{background:rgba(12,21,34,.78)}
    #nexus-3d-container{background:radial-gradient(ellipse at center,rgba(115,151,194,.17),transparent 68%)!important}.graph-view{position:relative;border:1px solid var(--line)!important;box-shadow:0 18px 55px rgba(0,0,0,.25)!important}
    .graph-view:after{content:"PETER MEMORY FIELD · LIVE";position:absolute;top:14px;left:16px;z-index:1;pointer-events:none;color:rgba(203,223,246,.48);font:9px ui-monospace,monospace;letter-spacing:.16em}
    .graph-toolbar,.graph-bottom,.graph-legend{backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px)}.graph-toolbar{background:rgba(8,13,22,.58)!important;border:1px solid rgba(255,255,255,.08)!important}
    .reasoning{line-height:1.6!important;color:#b9c9dc!important}.msg{line-height:1.55;white-space:pre-wrap;word-break:break-word}.commandbar{border-radius:18px!important}.commandbar input{min-width:0}.btn.primary{box-shadow:0 5px 22px rgba(83,211,255,.18)}

    /* RESPONSIVE VISUAL HUD IMAGE & SEARCH CARDS */
    .peter-image-view{width:100%;height:100%;display:flex;flex-direction:column;gap:10px;color:#f7f8fc;min-height:0}
    .peter-image-header{display:flex;align-items:center;justify-content:space-between;gap:8px}
    .peter-image-header h3{margin:0;color:#e4f2ff;font-size:13px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
    .peter-image-header a{color:var(--cyan);font:11px ui-monospace,monospace;text-decoration:none;white-space:nowrap}
    .peter-image-stage{position:relative;flex:1 1 auto;min-height:190px;max-height:300px;display:flex;align-items:center;justify-content:center;background:rgba(3,7,14,.55);border:1px solid rgba(131,232,244,.16);border-radius:12px;overflow:hidden;padding:6px}
    .peter-image-stage img{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain;border-radius:8px;transition:opacity .2s ease}
    .peter-image-thumbs{display:flex;gap:8px;overflow-x:auto;padding-bottom:2px;flex-shrink:0}
    .peter-image-thumb{width:58px;height:44px;object-fit:cover;border-radius:8px;border:1px solid rgba(255,255,255,.14);cursor:pointer;opacity:.72;transition:all .15s ease;flex-shrink:0;background:#0a111d}
    .peter-image-thumb:hover,.peter-image-thumb.active{opacity:1;border-color:var(--cyan);transform:translateY(-1px)}
    .peter-image-caption{font-size:11.5px;color:#a8bbd2;line-height:1.45;max-height:64px;overflow-y:auto;padding-right:4px}
    .peter-search-card{width:100%;height:100%;display:flex;flex-direction:column;gap:10px;overflow-y:auto;padding:4px}
    .peter-search-card h3{margin:0;font-size:13px;color:var(--cyan);font-family:ui-monospace,monospace}
    .peter-search-body{font-size:12.5px;line-height:1.55;color:#cfe0f5;white-space:pre-wrap}

    .route-pending{opacity:.72}.route-pending:before{content:"";display:inline-block;width:7px;height:7px;margin-right:8px;border-radius:50%;background:var(--cyan);box-shadow:0 0 12px var(--cyan);animation:peterPulse 1s infinite alternate}@keyframes peterPulse{to{opacity:.25}}
    .nexus-multi-graphs{margin:10px 0 14px}.nexus-graph-tabs{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px}.nexus-graph-tab{border:1px solid var(--line);border-radius:12px;background:rgba(14,24,38,.85);color:#d8eaff;padding:10px 14px;font:600 11px ui-monospace,monospace;letter-spacing:.05em;cursor:pointer}.nexus-graph-tab.active{background:rgba(83,211,255,.15);border-color:rgba(83,211,255,.5);color:#a8f4ff}.nexus-graph-caption{color:#aabbd0;font-size:12px;margin:0 0 9px}.nexus-graph-count{float:right;color:#9eb4cb;font:10px ui-monospace,monospace}.nexus-graph-canvas{height:min(68vh,720px);min-height:390px;border:1px solid var(--line);border-radius:16px;overflow:hidden;background:radial-gradient(ellipse at center,rgba(54,91,130,.18),rgba(4,8,15,.96) 70%)}.nexus-graph-error{padding:24px;color:#e6b5b5;font-size:13px}.graph-view.peter-legacy-hidden{display:none!important}

    @media(max-width:1100px){
      .dashboard-grid{grid-template-columns:1fr!important}
      .hud-card{min-height:340px!important}
    }
    @media(max-width:760px){
      .dashboard-grid{grid-template-columns:1fr!important}
      .hud-card{min-height:310px!important}
      .hud-content{min-height:240px!important}
      .peter-image-stage{min-height:160px;max-height:230px}
      .nexus-graph-canvas{height:65vh;min-height:360px}
      .nexus-graph-tab{flex:1 1 calc(50% - 8px)}
    }
    @media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.01ms!important;transition:none!important;scroll-behavior:auto!important}}
  `;
  document.head.appendChild(style);

  const warmConnection = () => fetch('/ping', { method: 'GET', cache: 'no-store' }).catch(() => {});
  if ('requestIdleCallback' in window) requestIdleCallback(warmConnection, { timeout: 1200 });
  else setTimeout(warmConnection, 300);

  const box = () => document.getElementById('hud-screen-content');

  function showImage(screen) {
    const container = box();
    if (!container || !screen?.image_url) return;

    const gallery = Array.isArray(screen.images) && screen.images.length
      ? screen.images
      : [{ title: screen.title, image_url: screen.image_url, thumbnail_url: screen.thumbnail_url || screen.image_url, source_url: screen.source_url || '' }];

    let currentIndex = 0;

    const root = document.createElement('div');
    root.className = 'peter-image-view';

    const header = document.createElement('div');
    header.className = 'peter-image-header';
    const title = document.createElement('h3');
    title.textContent = screen.title || 'Visual Feed';
    const sourceLink = document.createElement('a');
    sourceLink.target = '_blank';
    sourceLink.rel = 'noopener noreferrer';
    sourceLink.textContent = 'Fonte ↗';
    header.append(title, sourceLink);

    const stage = document.createElement('div');
    stage.className = 'peter-image-stage';
    const mainImg = document.createElement('img');
    mainImg.alt = screen.title || 'Immagine';
    stage.append(mainImg);

    const thumbsBar = document.createElement('div');
    thumbsBar.className = 'peter-image-thumbs';

    const caption = document.createElement('div');
    caption.className = 'peter-image-caption';
    caption.textContent = screen.content || '';

    function selectImage(idx) {
      const item = gallery[idx];
      if (!item) return;
      currentIndex = idx;
      title.textContent = item.title || screen.title || 'Visual Feed';
      if (item.source_url) {
        sourceLink.href = item.source_url;
        sourceLink.style.display = 'inline';
      } else {
        sourceLink.style.display = 'none';
      }

      let triedThumb = false;
      mainImg.onerror = () => {
        if (!triedThumb && item.thumbnail_url && mainImg.src !== item.thumbnail_url) {
          triedThumb = true;
          mainImg.src = item.thumbnail_url;
        } else if (currentIndex + 1 < gallery.length) {
          selectImage(currentIndex + 1);
        } else {
          caption.textContent = 'Anteprima bloccata dal sito sorgente. Prova a chiedere un modello specifico.';
        }
      };
      mainImg.src = item.image_url;

      thumbsBar.querySelectorAll('.peter-image-thumb').forEach((el, i) => {
        el.classList.toggle('active', i === idx);
      });
    }

    if (gallery.length > 1) {
      gallery.forEach((item, idx) => {
        const t = document.createElement('img');
        t.className = 'peter-image-thumb' + (idx === 0 ? ' active' : '');
        t.src = item.thumbnail_url || item.image_url;
        t.alt = item.title || `Anteprima ${idx + 1}`;
        t.onerror = () => { t.style.display = 'none'; };
        t.onclick = () => selectImage(idx);
        thumbsBar.append(t);
      });
    }

    root.append(header, stage);
    if (gallery.length > 1) root.append(thumbsBar);
    if (screen.content) root.append(caption);

    container.replaceChildren(root);
    selectImage(0);

    const badge = document.getElementById('hud-status-badge');
    if (badge) badge.textContent = 'ACTIVE // IMAGE_PREVIEW';
  }

  function showSearchPreview(screen) {
    const container = box();
    if (!container) return;
    const card = document.createElement('div');
    card.className = 'peter-search-card';
    const h = document.createElement('h3');
    h.textContent = `WEB INTEL // ${(screen.query || 'RICERCA').toUpperCase()}`;
    const body = document.createElement('div');
    body.className = 'peter-search-body';
    body.textContent = screen.content || 'Nessun dettaglio testuale disponibile.';
    card.append(h, body);
    container.replaceChildren(card);
    const badge = document.getElementById('hud-status-badge');
    if (badge) badge.textContent = 'ACTIVE // WEB_INTEL';
  }

  function installHudHook() {
    const originalUpdateHud = window.updateHudScreen;
    if (typeof originalUpdateHud !== 'function') {
      setTimeout(installHudHook, 30);
      return;
    }
    if (originalUpdateHud.__peterEnhancedHook) return;
    const wrapped = screen => {
      if (screen?.type === 'IMAGE_PREVIEW' && screen.image_url) {
        showImage(screen);
        return;
      }
      if (screen?.type === 'SEARCH_PREVIEW') {
        showSearchPreview(screen);
        return;
      }
      return originalUpdateHud(screen);
    };
    wrapped.__peterEnhancedHook = true;
    window.updateHudScreen = wrapped;
  }
  installHudHook();

  // Mantiene intatti tutti i grafi 3D di Neural Nexus
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
