/* Peter OS v11 — iOS 27 Liquid Glass UI, Structured Memory Core & Intelligent HUD */
(() => {
  'use strict';

  const style = document.createElement('style');
  style.textContent = `
    :root{
      --bg:#060a12;
      --glass:rgba(18,26,40,.62);
      --glass-strong:rgba(22,32,48,.78);
      --glass-border:rgba(255,255,255,.14);
      --glass-highlight:rgba(255,255,255,.06);
      --cyan:#6ce5ff;
      --blue:#5e9eff;
      --violet:#b89cff;
      --green:#6ee7b7;
      --amber:#fcd34d;
      --text:#f3f7ff;
      --muted:#96a8c2;
      --squircle:22px;
    }
    body{
      background:
        radial-gradient(circle at 18% -10%, rgba(94,158,255,.26), transparent 44%),
        radial-gradient(circle at 86% 12%, rgba(108,229,255,.18), transparent 38%),
        radial-gradient(circle at 75% 92%, rgba(184,156,255,.18), transparent 42%),
        #060a12 !important;
      color:var(--text) !important;
      font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Inter",system-ui,sans-serif !important;
    }
    .topbar,.panel,.commandbar,.settings-card,.graph-view{
      background:var(--glass) !important;
      backdrop-filter:blur(26px) saturate(180%) !important;
      -webkit-backdrop-filter:blur(26px) saturate(180%) !important;
      border:1px solid var(--glass-border) !important;
      box-shadow:0 20px 50px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.12) !important;
    }
    .topbar,.panel,.settings-card,.graph-view{border-radius:var(--squircle) !important;}
    .sidebar{
      background:rgba(12,18,30,.66) !important;
      backdrop-filter:blur(28px) saturate(180%) !important;
      -webkit-backdrop-filter:blur(28px) saturate(180%) !important;
      border-right:1px solid rgba(255,255,255,.1) !important;
    }
    .nav-btn,.btn,.filter-btn,.icon-btn,.commandbar button{
      border-radius:14px !important;
      border:1px solid rgba(255,255,255,.1) !important;
      background:rgba(255,255,255,.05) !important;
      transition:all .2s cubic-bezier(.2,.8,.2,1) !important;
    }
    .nav-btn:hover,.btn:hover,.filter-btn:hover,.icon-btn:hover{
      transform:translateY(-1px);
      background:rgba(255,255,255,.11) !important;
      border-color:rgba(255,255,255,.22) !important;
    }
    .nav-btn.active,.filter-btn.active{
      background:linear-gradient(135deg,rgba(108,229,255,.22),rgba(94,158,255,.18)) !important;
      border-color:rgba(108,229,255,.45) !important;
      box-shadow:0 6px 20px rgba(94,158,255,.2) !important;
    }
    .dashboard-grid{grid-template-columns:minmax(0,1.06fr) minmax(330px,.94fr) !important;gap:16px !important;}
    .side-stack{min-width:0;display:flex !important;flex-direction:column !important;gap:16px !important;}
    .hud-card{min-height:370px !important;display:flex !important;flex-direction:column !important;}
    .hud-content{flex:1 1 auto !important;min-height:285px !important;display:flex !important;flex-direction:column !important;overflow:hidden !important;}
    .msg{
      border-radius:18px !important;
      line-height:1.55 !important;
      white-space:pre-wrap;
      word-break:break-word;
      backdrop-filter:blur(12px);
    }
    .commandbar{
      border-radius:24px !important;
      padding:8px 10px !important;
      background:var(--glass-strong) !important;
    }
    .btn.primary{
      background:linear-gradient(135deg,#5e9eff,#38bdf8) !important;
      color:#04101f !important;
      font-weight:700 !important;
      border:none !important;
      box-shadow:0 8px 24px rgba(56,189,248,.32) !important;
    }

    /* VISUAL HUD COMPONENTS (IMAGE, SEARCH, SYSTEM BRIEF) */
    .peter-image-view{width:100%;height:100%;display:flex;flex-direction:column;gap:10px;color:var(--text);min-height:0;}
    .peter-image-header{display:flex;align-items:center;justify-content:space-between;gap:8px;}
    .peter-image-header h3{margin:0;color:#eef6ff;font-size:13.5px;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
    .peter-image-header a{color:var(--cyan);font:600 11px ui-monospace,monospace;text-decoration:none;white-space:nowrap;}
    .peter-image-stage{position:relative;flex:1 1 auto;min-height:190px;max-height:290px;display:flex;align-items:center;justify-content:center;background:rgba(4,8,16,.52);border:1px solid rgba(255,255,255,.12);border-radius:16px;overflow:hidden;padding:8px;}
    .peter-image-stage img{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain;border-radius:10px;}
    .peter-image-thumbs{display:flex;gap:8px;overflow-x:auto;padding-bottom:2px;flex-shrink:0;}
    .peter-image-thumb{width:56px;height:42px;object-fit:cover;border-radius:10px;border:1px solid rgba(255,255,255,.15);cursor:pointer;opacity:.68;transition:all .15s ease;flex-shrink:0;background:#09101d;}
    .peter-image-thumb:hover,.peter-image-thumb.active{opacity:1;border-color:var(--cyan);transform:scale(1.04);}
    .peter-image-caption{font-size:11.5px;color:#b2c4dc;line-height:1.45;max-height:60px;overflow-y:auto;}

    .peter-brief-card{
      width:100%;height:100%;display:flex;flex-direction:column;justify-content:space-between;gap:12px;
      padding:16px;border-radius:18px;
      background:linear-gradient(155deg,rgba(94,158,255,.12),rgba(18,26,40,.55));
      border:1px solid rgba(255,255,255,.12);
    }
    .peter-brief-kicker{font:600 10px ui-monospace,monospace;letter-spacing:.14em;color:var(--cyan);}
    .peter-brief-title{font-size:16px;font-weight:700;color:#fff;margin:2px 0;}
    .peter-brief-list{display:flex;flex-direction:column;gap:8px;margin:0;padding:0;list-style:none;}
    .peter-brief-list li{
      padding:9px 12px;border-radius:12px;background:rgba(255,255,255,.05);
      border:1px solid rgba(255,255,255,.08);font-size:12px;color:#d6e4f7;line-height:1.45;
    }

    /* IOS 27 MEMORY CORE REDESIGN */
    .ios-mem-shell{display:flex;flex-direction:column;gap:14px;margin-top:6px;}
    .ios-mem-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;}
    .ios-stat-pill{
      padding:12px 14px;border-radius:18px;
      background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.11);
      display:flex;flex-direction:column;gap:4px;cursor:pointer;transition:all .18s ease;
    }
    .ios-stat-pill:hover,.ios-stat-pill.active{
      background:rgba(108,229,255,.14);border-color:rgba(108,229,255,.45);transform:translateY(-1px);
    }
    .ios-stat-num{font-size:20px;font-weight:700;color:#fff;}
    .ios-stat-lbl{font:600 10.5px ui-monospace,monospace;color:var(--muted);letter-spacing:.06em;}
    .ios-mem-toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;}
    .ios-mem-search{
      flex:1 1 240px;padding:10px 14px;border-radius:14px;
      background:rgba(8,13,24,.65);border:1px solid rgba(255,255,255,.14);
      color:#fff;font-size:13px;outline:none;
    }
    .ios-mem-search:focus{border-color:var(--cyan);}
    .ios-mem-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:12px;max-height:58vh;overflow-y:auto;padding-right:4px;}
    .ios-mem-card{
      padding:14px;border-radius:18px;background:rgba(255,255,255,.045);
      border:1px solid rgba(255,255,255,.1);display:flex;flex-direction:column;gap:8px;
    }
    .ios-mem-badge{
      align-self:flex-start;padding:3px 9px;border-radius:999px;font:600 10px ui-monospace,monospace;
      background:rgba(108,229,255,.14);color:var(--cyan);border:1px solid rgba(108,229,255,.28);
    }
    .ios-mem-text{font-size:13px;line-height:1.5;color:#e8f0fc;white-space:pre-wrap;word-break:break-word;}
    .ios-mem-actions{display:flex;gap:8px;margin-top:auto;padding-top:6px;}
    .ios-mini-btn{
      padding:5px 10px;border-radius:10px;font-size:11px;cursor:pointer;
      background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);color:#dce8fa;
    }
    .ios-mini-btn.danger{color:#fda4af;border-color:rgba(253,164,175,.3);}

    /* NEXUS 3D */
    .nexus-multi-graphs{margin:10px 0 14px}.nexus-graph-tabs{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px}.nexus-graph-tab{border:1px solid var(--glass-border);border-radius:14px;background:rgba(14,24,38,.75);color:#d8eaff;padding:10px 14px;font:600 11px ui-monospace,monospace;letter-spacing:.05em;cursor:pointer}.nexus-graph-tab.active{background:rgba(108,229,255,.18);border-color:rgba(108,229,255,.5);color:#fff}.nexus-graph-caption{color:#aabbd0;font-size:12px;margin:0 0 9px}.nexus-graph-count{float:right;color:#9eb4cb;font:10px ui-monospace,monospace}.nexus-graph-canvas{height:min(68vh,720px);min-height:390px;border:1px solid var(--glass-border);border-radius:20px;overflow:hidden;background:radial-gradient(ellipse at center,rgba(54,91,130,.18),rgba(4,8,15,.96) 70%)}.nexus-graph-error{padding:24px;color:#e6b5b5;font-size:13px}.graph-view.peter-legacy-hidden{display:none!important}

    @media(max-width:1100px){.dashboard-grid{grid-template-columns:1fr !important;}}
    @media(max-width:760px){
      .ios-mem-stats{grid-template-columns:repeat(2,minmax(0,1fr));}
      .peter-image-stage{min-height:160px;max-height:220px;}
    }
  `;
  document.head.appendChild(style);

  // Keep-Alive browser ping ogni 4 minuti finché la dashboard è aperta
  const pingServer = () => fetch('/ping', { method: 'GET', cache: 'no-store' }).catch(() => {});
  pingServer();
  setInterval(pingServer, 240000);

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
          caption.textContent = 'Immagine protetta dal server esterno. Prova un altro risultato dalle miniature.';
        }
      };
      mainImg.src = item.image_url;
      thumbsBar.querySelectorAll('.peter-image-thumb').forEach((el, i) => el.classList.toggle('active', i === idx));
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
    if (badge) badge.textContent = 'ACTIVE // IMAGE_HUD';
  }

  function showSearchPreview(screen) {
    const container = box();
    if (!container) return;
    const card = document.createElement('div');
    card.className = 'peter-brief-card';
    card.innerHTML = `
      <div>
        <div class="peter-brief-kicker">WEB INTEL // VERIFIED</div>
        <div class="peter-brief-title">${(screen.query || 'Ricerca').toUpperCase()}</div>
      </div>
      <div style="font-size:12.5px;line-height:1.55;color:#dbe8fa;overflow-y:auto;white-space:pre-wrap;">${screen.content || 'Nessun dettaglio trovato.'}</div>
    `;
    container.replaceChildren(card);
    const badge = document.getElementById('hud-status-badge');
    if (badge) badge.textContent = 'ACTIVE // WEB_INTEL';
  }

  function showSystemBrief(screen) {
    const container = box();
    if (!container) return;
    const items = Array.isArray(screen.highlights) ? screen.highlights : [];
    const card = document.createElement('div');
    card.className = 'peter-brief-card';
    const listHtml = items.map(i => `<li>${i}</li>`).join('');
    card.innerHTML = `
      <div>
        <div class="peter-brief-kicker">${screen.subtitle || 'PETER OS // LIVE'}</div>
        <div class="peter-brief-title">${screen.title || 'NEURAL HUD'}</div>
      </div>
      <ul class="peter-brief-list">${listHtml}</ul>
    `;
    container.replaceChildren(card);
    const badge = document.getElementById('hud-status-badge');
    if (badge) badge.textContent = 'ACTIVE // CONTEXT_HUD';
  }

  function installHudHook() {
    const originalUpdateHud = window.updateHudScreen;
    if (typeof originalUpdateHud !== 'function') {
      setTimeout(installHudHook, 30);
      return;
    }
    if (originalUpdateHud.__peterIos27Hook) return;
    const wrapped = screen => {
      if (screen?.type === 'IMAGE_PREVIEW' && screen.image_url) {
        showImage(screen);
        return;
      }
      if (screen?.type === 'SEARCH_PREVIEW') {
        showSearchPreview(screen);
        return;
      }
      if (screen?.type === 'SYSTEM_BRIEF') {
        showSystemBrief(screen);
        return;
      }
      return originalUpdateHud(screen);
    };
    wrapped.__peterIos27Hook = true;
    window.updateHudScreen = wrapped;
  }
  installHudHook();

  // --- REDESIGN COMPLETO MEMORY CORE (4 DOMINI COGNITIVI STILE IOS 27) ---
  function initMemoryCoreUI() {
    const memView = document.getElementById('view-memories');
    if (!memView || memView.dataset.ios27Ready) return;
    memView.dataset.ios27Ready = '1';

    const shell = document.createElement('div');
    shell.className = 'ios-mem-shell';
    shell.innerHTML = `
      <div class="ios-mem-stats">
        <div class="ios-stat-pill active" data-domain="semantic">
          <span class="ios-stat-num" id="mem-count-semantic">0</span>
          <span class="ios-stat-lbl">SEMANTICA · FATTI</span>
        </div>
        <div class="ios-stat-pill" data-domain="social">
          <span class="ios-stat-num" id="mem-count-social">0</span>
          <span class="ios-stat-lbl">SOCIALE · PERSONE</span>
        </div>
        <div class="ios-stat-pill" data-domain="temporal">
          <span class="ios-stat-num" id="mem-count-temporal">0</span>
          <span class="ios-stat-lbl">TEMPORALE · EVENTI</span>
        </div>
        <div class="ios-stat-pill" data-domain="episodic">
          <span class="ios-stat-num" id="mem-count-episodic">0</span>
          <span class="ios-stat-lbl">EPISODICA · CHAT</span>
        </div>
      </div>
      <div class="ios-mem-toolbar">
        <input type="search" class="ios-mem-search" id="ios-mem-filter" placeholder="Cerca nei ricordi di Peter...">
        <button type="button" class="btn" id="ios-mem-refresh">Aggiorna Memoria</button>
      </div>
      <div class="ios-mem-grid" id="ios-mem-grid"></div>
    `;

    // Nasconde eventuali vecchi contenitori grezzi e inserisce la nuova shell iOS 27
    Array.from(memView.children).forEach(child => {
      if (!child.classList.contains('view-heading')) child.style.display = 'none';
    });
    memView.append(shell);

    let memoryData = { semantic: [], social: [], temporal: [], episodic: [] };
    let activeDomain = 'semantic';

    function renderCards() {
      const grid = document.getElementById('ios-mem-grid');
      const query = (document.getElementById('ios-mem-filter')?.value || '').toLowerCase().trim();
      if (!grid) return;

      const list = memoryData[activeDomain] || [];
      const filtered = list.filter(item => JSON.stringify(item).toLowerCase().includes(query));

      if (!filtered.length) {
        grid.innerHTML = '<div style="padding:20px;color:#96a8c2;font-size:13px;">Nessun elemento in questo dominio di memoria.</div>';
        return;
      }

      grid.replaceChildren();
      filtered.forEach(item => {
        const card = document.createElement('div');
        card.className = 'ios-mem-card';

        if (activeDomain === 'semantic') {
          card.innerHTML = `
            <span class="ios-mem-badge">FATTO A LUNGO TERMINE</span>
            <div class="ios-mem-text">${item.fact || ''}</div>
          `;
          const actions = document.createElement('div');
          actions.className = 'ios-mem-actions';

          const editBtn = document.createElement('button');
          editBtn.className = 'ios-mini-btn';
          editBtn.textContent = 'Modifica';
          editBtn.onclick = async () => {
            const updated = prompt('Modifica ricordo:', item.fact || '');
            if (updated && updated.trim()) {
              await fetch(`/api/facts/${item.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fact: updated.trim() })
              });
              loadStructuredMemories();
            }
          };

          const delBtn = document.createElement('button');
          delBtn.className = 'ios-mini-btn danger';
          delBtn.textContent = 'Elimina';
          delBtn.onclick = async () => {
            await fetch(`/api/facts/${item.id}`, { method: 'DELETE' });
            loadStructuredMemories();
          };

          actions.append(editBtn, delBtn);
          card.append(actions);
        } else if (activeDomain === 'social') {
          card.innerHTML = `
            <span class="ios-mem-badge">${(item.relation_type || item.category || 'CONTATTO').toUpperCase()}</span>
            <div style="font-weight:700;font-size:14px;color:#fff;">${item.name || ''}</div>
            <div class="ios-mem-text">${item.notes || 'Nessuna nota aggiuntiva.'}</div>
          `;
        } else if (activeDomain === 'temporal') {
          card.innerHTML = `
            <span class="ios-mem-badge">${(item.kind || 'EVENTO').toUpperCase()} · ${item.when || ''}</span>
            <div style="font-weight:700;font-size:14px;color:#fff;">${item.title || ''}</div>
            <div class="ios-mem-text">${item.detail || ''}</div>
          `;
        } else {
          card.innerHTML = `
            <span class="ios-mem-badge">EPISODIO CONVERSAZIONE</span>
            <div class="ios-mem-text">${item.content || ''}</div>
          `;
        }

        grid.append(card);
      });
    }

    async function loadStructuredMemories() {
      try {
        const res = await fetch('/api/memories/structured', { cache: 'no-store' });
        if (!res.ok) return;
        const data = await res.json();
        memoryData = data;
        document.getElementById('mem-count-semantic').textContent = data.stats?.semantic ?? 0;
        document.getElementById('mem-count-social').textContent = data.stats?.social ?? 0;
        document.getElementById('mem-count-temporal').textContent = data.stats?.temporal ?? 0;
        document.getElementById('mem-count-episodic').textContent = data.stats?.episodic ?? 0;
        renderCards();
      } catch (e) {
        console.warn('Errore caricamento memorie strutturate:', e);
      }
    }

    shell.querySelectorAll('.ios-stat-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        shell.querySelectorAll('.ios-stat-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        activeDomain = pill.dataset.domain;
        renderCards();
      });
    });

    document.getElementById('ios-mem-filter')?.addEventListener('input', renderCards);
    document.getElementById('ios-mem-refresh')?.addEventListener('click', loadStructuredMemories);
    document.querySelector('.nav-btn[data-view="memories"]')?.addEventListener('click', loadStructuredMemories);
    loadStructuredMemories();
  }
  initMemoryCoreUI();

  // --- NEURAL NEXUS 3D (MANTIENE TUTTE LE 4 VISTE) ---
  const graphView = document.getElementById('view-nexus');
  if (graphView) {
    const legacy = graphView.querySelector('.graph-view');
    const multi = document.createElement('section');
    multi.className = 'nexus-multi-graphs';
    multi.innerHTML = '<div class="nexus-graph-tabs" role="tablist"></div><p class="nexus-graph-caption"></p><div class="nexus-graph-canvas"></div>';
    if (legacy) { legacy.classList.add('peter-legacy-hidden'); legacy.insertAdjacentElement('beforebegin', multi); }
    else graphView.append(multi);

    const tabs = multi.querySelector('.nexus-graph-tabs');
    const caption = multi.querySelector('.nexus-graph-caption');
    const canvas = multi.querySelector('.nexus-graph-canvas');
    const views = [
      { id: 'family', label: 'ALBERO FAMILIARE', caption: 'Legami familiari espliciti tra genitori e figli.' },
      { id: 'people', label: 'PERSONE E RELAZIONI', caption: 'Amici, colleghi e conoscenti collegati per relazione.' },
      { id: 'chats', label: 'TUTTE LE CHAT', caption: 'Sequenza cronologica delle conversazioni.' },
      { id: 'facts', label: 'RICORDI A LUNGO TERMINE', caption: 'Mappa radiale dei fatti consolidati.' },
    ];
    let graph = null;
    let activeView = null;
    let loadToken = 0;
    const color = node => node.type === 'core' ? '#32e6ac' : node.type === 'person' ? (node.relationship_group === 'family' ? '#ff6fbe' : '#5e9eff') : node.type === 'chat' ? '#6ce5ff' : '#b89cff';
    function disposeGraph() { if (graph) { graph._destructor?.(); graph = null; } }

    async function renderView(view) {
      activeView = view.id;
      const token = ++loadToken;
      caption.textContent = view.caption;
      tabs.querySelectorAll('button').forEach(b => b.classList.toggle('active', b.dataset.view === view.id));
      canvas.replaceChildren();
      disposeGraph();
      if (typeof ForceGraph3D !== 'function') {
        canvas.innerHTML = '<div class="nexus-graph-error">Libreria 3D non disponibile.</div>';
        return;
      }
      canvas.innerHTML = '<div class="nexus-graph-error">Caricamento grafo 3D…</div>';
      try {
        const response = await fetch(`/api/nexus/${view.id}`, { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        if (token !== loadToken || activeView !== view.id) return;
        const nodes = Array.isArray(data.nodes) ? data.nodes : [];
        const nodeIds = new Set(nodes.map(n => String(n.id)));
        const links = (Array.isArray(data.edges) ? data.edges : [])
          .filter(e => nodeIds.has(String(e.source?.id ?? e.source)) && nodeIds.has(String(e.target?.id ?? e.target)))
          .map(e => ({ ...e, source: String(e.source?.id ?? e.source), target: String(e.target?.id ?? e.target) }));
        caption.innerHTML = `${view.caption}<span class="nexus-graph-count">${nodes.length} NODI · ${links.length} LEGAMI</span>`;
        canvas.replaceChildren();
        if (!nodes.length) {
          canvas.innerHTML = '<div class="nexus-graph-error">Nessun dato salvato per questa vista.</div>';
          return;
        }
        graph = ForceGraph3D()(canvas)
          .backgroundColor('rgba(3,7,13,0)')
          .graphData({ nodes, links })
          .nodeId('id')
          .nodeLabel(n => `${n.name || n.id}${n.relation_type ? ` · ${n.relation_type}` : ''}`)
          .nodeColor(color)
          .nodeVal(n => n.type === 'core' ? 12 : view.id === 'chats' ? 4 : 7)
          .linkColor(l => String(l.category || '').includes('famiglia') ? '#32e6ac' : '#7c95b4')
          .linkOpacity(.65)
          .linkDirectionalParticles(2)
          .linkDirectionalParticleWidth(2)
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
      } catch (err) {
        if (token === loadToken) canvas.innerHTML = `<div class="nexus-graph-error">Errore grafo: ${String(err.message || err)}</div>`;
      }
    }

    views.forEach(view => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'nexus-graph-tab';
      btn.dataset.view = view.id;
      btn.textContent = view.label;
      btn.addEventListener('click', () => renderView(view));
      tabs.append(btn);
    });

    const resizeObserver = new ResizeObserver(() => graph?.width(canvas.clientWidth).height(canvas.clientHeight));
    resizeObserver.observe(canvas);
    document.querySelector('.nav-btn[data-view="nexus"]')?.addEventListener('click', () => { if (!activeView) renderView(views[0]); }, { once: true });
    if (graphView.classList.contains('active')) renderView(views[0]);
  }
})();
