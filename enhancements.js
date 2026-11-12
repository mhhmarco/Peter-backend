/* Peter HUD responsive media and second-brain polish. */
(() => {
  'use strict';
  const style = document.createElement('style');
  style.textContent = `
    .dashboard-grid{grid-template-columns:minmax(0,1fr) minmax(360px,1.08fr)!important;gap:14px!important}
    .side-stack{min-width:0;grid-template-rows:minmax(340px,1fr) auto auto!important}
    .hud-card{min-height:440px!important;display:flex;flex-direction:column}
    .hud-content{flex:1;min-height:350px!important;overflow:hidden}
    .peter-player{width:100%!important;max-width:none!important;min-height:100%!important;gap:10px!important}
    .peter-player-frame{min-height:260px!important;aspect-ratio:16/9;flex:1 1 auto!important}
    .peter-player-title{font-size:14px!important}
    .brain-status{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 8px}
    .brain-chip{border:1px solid var(--line);border-radius:999px;padding:5px 9px;color:var(--cyan);background:rgba(10,18,32,.8);font:10px ui-monospace,monospace}
    #nexus-3d-container{background:radial-gradient(ellipse at center,rgba(30,75,105,.24),transparent 65%)!important}
    .graph-view{border:1px solid var(--line);box-shadow:inset 0 0 45px rgba(48,180,255,.06)}
    .inspector{backdrop-filter:blur(16px);box-shadow:0 16px 48px rgba(0,0,0,.4)}
    .peter-image-view{width:100%;height:100%;min-height:280px;display:grid;grid-template-rows:auto minmax(0,1fr);gap:10px;color:var(--text,#f8fafc)}
    .peter-image-view h3{margin:0;color:var(--cyan);font-size:14px}
    .peter-image-body{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(130px,.8fr);gap:14px;min-height:0;align-items:center}
    .peter-image-body img{width:100%;height:100%;max-height:460px;object-fit:contain;background:#030711;border-radius:12px;border:1px solid var(--line)}
    .peter-image-info{font-size:11px;color:var(--muted);overflow:auto;max-height:100%}
    .peter-image-info a{color:var(--cyan)}
    @media(max-width:1100px){.dashboard-grid{grid-template-columns:1fr!important}.side-stack{grid-template-rows:minmax(360px,1fr) auto auto!important}.hud-card{min-height:420px!important}}
    @media(max-width:760px){.dashboard-grid{grid-template-columns:1fr!important}.side-stack{display:grid;grid-template-columns:1fr!important}.hud-card{min-height:390px!important}.hud-content{min-height:310px!important}.peter-player-frame{min-height:190px!important}.peter-image-body{grid-template-columns:1fr;grid-template-rows:minmax(180px,1fr) auto}.peter-image-body img{max-height:300px}}
  `;
  document.head.appendChild(style);

  const box = () => document.getElementById('hud-screen-content');
  function showImage(screen) {
    const container = box();
    if (!container || !screen?.image_url) return;
    const root = document.createElement('div'); root.className = 'peter-image-view';
    const title = document.createElement('h3'); title.textContent = screen.title || 'Immagine';
    const body = document.createElement('div'); body.className = 'peter-image-body';
    const img = document.createElement('img'); img.src = screen.image_url; img.alt = screen.title || 'Immagine trovata'; img.loading = 'eager';
    const info = document.createElement('div'); info.className = 'peter-image-info';
    info.textContent = screen.content || 'Immagine trovata sul web.';
    if (screen.source_url) { const link = document.createElement('a'); link.href = screen.source_url; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = 'Apri fonte ↗'; info.append(document.createElement('br'), link); }
    body.append(img, info); root.append(title, body); container.replaceChildren(root);
    const badge = document.getElementById('hud-status-badge'); if (badge) badge.textContent = 'ACTIVE // IMAGE';
    img.addEventListener('error', () => { info.textContent = 'Questa immagine non è accessibile direttamente. Prova un’altra ricerca.'; }, {once:true});
  }
  const original = window.updateHudScreen;
  if (typeof original === 'function') window.updateHudScreen = screen => {
    if (screen?.type === 'IMAGE_PREVIEW' && screen.image_url) { showImage(screen); return; }
    return original(screen);
  };

  // Image intent is handled separately, while Peter's normal response and reasoning layers remain intact.
  const input = document.getElementById('cmd-input');
  const send = document.getElementById('send-cmd-btn');
  let busy = false;
  const imageIntent = text => /\b(immagin(?:e|i)|foto|fotografie|mostra(?:mi)?|cerca)\b/i.test(text) && /\b(immagin(?:e|i)|foto|fotografie)\b/i.test(text);
  async function sendImageRequest(event) {
    if (!input || !imageIntent(input.value.trim()) || busy) return;
    event.preventDefault(); event.stopImmediatePropagation(); busy = true;
    const message = input.value.trim(); input.value = '';
    const feed = document.getElementById('chat-feed');
    const append = (text, kind='peter') => { if (!feed) return; const el=document.createElement('div'); el.className=`msg ${kind}`; el.textContent=text; feed.append(el); feed.scrollTop=feed.scrollHeight; };
    append(message, 'user');
    const form = new FormData(); form.append('message', message);
    try {
      const [imageResponse, chatResponse] = await Promise.all([
        fetch('/api/images/search', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({query:message})}),
        fetch('/chat', {method:'POST', body:form})
      ]);
      const image = await imageResponse.json(); const chat = await chatResponse.json();
      if (!chatResponse.ok) throw new Error(chat.detail || 'Richiesta non riuscita');
      append(chat.reply || 'Risposta vuota');
      if (chat.reasoning) { const r=document.getElementById('reasoning-preview'); if(r) r.textContent=chat.reasoning; }
      if (image.image_url) { showImage({type:'IMAGE_PREVIEW', ...image}); }
      else if (chat.screen && typeof window.updateHudScreen === 'function') window.updateHudScreen(chat.screen);
    } catch (error) { append(`Errore: ${error.message}`, 'system'); }
    finally { busy = false; if(send) send.disabled=false; input.focus(); }
  }
  if (send) send.addEventListener('click', sendImageRequest, true);
  if (input) input.addEventListener('keydown', event => { if(event.key==='Enter'&&!event.shiftKey&&imageIntent(input.value.trim())) sendImageRequest(event); }, true);

  // Make live Supabase graph data feel like a navigable knowledge space.
  const graph = document.getElementById('view-nexus');
  if (graph) {
    const heading = graph.querySelector('.view-heading');
    if (heading) {
      const chips = document.createElement('div'); chips.className='brain-status';
      for (const [label,id] of [['NODES','node-count'],['CONNECTIONS','edge-count'],['SYNC','graph-status']]) {
        const chip=document.createElement('span'); chip.className='brain-chip';
        if(label==='SYNC'){ chip.id='brain-sync-chip'; chip.textContent='SUPABASE · LIVE'; }
        else { chip.textContent=`${label} · `; const count=document.createElement('b'); count.id=`brain-${id}`; count.textContent='0'; chip.append(count); }
        chips.append(chip);
      }
      heading.append(chips);
      const sync = document.getElementById('graph-status');
      if(sync){ new MutationObserver(()=>{ const target=document.getElementById('brain-sync-chip'); if(target) target.textContent=`SUPABASE · ${sync.textContent||'LIVE'}`; }).observe(sync,{childList:true,subtree:true,characterData:true}); }
      const updateCounts = () => { for(const id of ['node-count','edge-count']){const source=document.getElementById(id),target=document.getElementById(`brain-${id}`);if(source&&target)target.textContent=source.textContent;} };
      setInterval(updateCounts, 700);
    }
  }
})();
