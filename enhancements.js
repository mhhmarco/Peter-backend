/* Glass-like, iOS-inspired interface polish and integrated image HUD. */
(() => {
  'use strict';
  const style = document.createElement('style');
  style.textContent = `
    :root{--bg:#090b12;--panel:rgba(25,29,41,.72);--panel2:rgba(34,39,53,.72);--line:rgba(255,255,255,.12);--cyan:#a8d9ff;--blue:#8ebeff;--violet:#c3b4ff;--green:#a4e7c8;--amber:#f5d69c;--red:#ff9eae;--muted:#a9b0c0}
    body{background:radial-gradient(ellipse at 18% 0%,rgba(130,159,211,.19),transparent 40%),radial-gradient(ellipse at 85% 22%,rgba(157,133,204,.12),transparent 34%),#090b12!important}
    .panel,.topbar,.commandbar,.settings-card,.graph-view{background:rgba(27,31,43,.68)!important;border-color:rgba(255,255,255,.11)!important;box-shadow:0 12px 40px rgba(0,0,0,.22),inset 0 1px rgba(255,255,255,.04)!important;backdrop-filter:blur(24px) saturate(145%);-webkit-backdrop-filter:blur(24px) saturate(145%)}
    .nav-btn,.btn,.filter-btn,.icon-btn,.commandbar button{border-radius:999px!important;transition:background .18s ease,transform .18s ease,border-color .18s ease!important}
    .nav-btn:hover,.btn:hover,.filter-btn:hover,.icon-btn:hover{transform:translateY(-1px);background:rgba(255,255,255,.1)!important}
    .nav-btn.active,.filter-btn.active{background:rgba(156,198,255,.18)!important;color:#d9ecff!important;border-color:rgba(180,215,255,.25)!important}
    .dashboard-grid{grid-template-columns:minmax(0,1fr) minmax(360px,1.08fr)!important;gap:14px!important}
    .side-stack{min-width:0;grid-template-rows:minmax(350px,1fr) auto auto!important}
    .hud-card{min-height:450px!important;display:flex;flex-direction:column}
    .hud-content{flex:1;min-height:350px!important;overflow:hidden}
    .peter-player{width:100%!important;max-width:none!important;min-height:100%!important;gap:10px!important}
    .peter-player-frame{min-height:260px!important;aspect-ratio:16/9;flex:1 1 auto!important}
    .brain-status{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 8px}
    .brain-chip{border:1px solid rgba(255,255,255,.13);border-radius:999px;padding:6px 10px;color:#d8eaff;background:rgba(255,255,255,.06);font:10px ui-monospace,monospace}
    #nexus-3d-container{background:radial-gradient(ellipse at center,rgba(115,151,194,.17),transparent 68%)!important}
    .graph-view{border:1px solid var(--line);box-shadow:inset 0 0 55px rgba(174,209,255,.06)!important}
    .inspector{backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px);box-shadow:0 16px 48px rgba(0,0,0,.4)}
    .peter-image-view{width:100%;height:100%;min-height:280px;display:grid;grid-template-rows:auto minmax(0,1fr);gap:10px;color:#f7f8fc}
    .peter-image-view h3{margin:0;color:#e4f2ff;font-size:14px}
    .peter-image-body{display:grid;grid-template-columns:minmax(0,1.4fr) minmax(130px,.8fr);gap:14px;min-height:0;align-items:center}
    .peter-image-body img{width:100%;height:100%;max-height:460px;object-fit:contain;background:#090b12;border-radius:16px;border:1px solid rgba(255,255,255,.13)}
    .peter-image-info{font-size:11px;color:var(--muted);overflow:auto;max-height:100%}.peter-image-info a{color:#c8e5ff}
    @media(max-width:1100px){.dashboard-grid{grid-template-columns:1fr!important}.side-stack{grid-template-rows:minmax(360px,1fr) auto auto!important}.hud-card{min-height:420px!important}}
    @media(max-width:760px){.dashboard-grid{grid-template-columns:1fr!important}.side-stack{display:grid;grid-template-columns:1fr!important}.hud-card{min-height:390px!important}.hud-content{min-height:310px!important}.peter-player-frame{min-height:190px!important}.peter-image-body{grid-template-columns:1fr;grid-template-rows:minmax(180px,1fr) auto}.peter-image-body img{max-height:300px}}
    @media(prefers-reduced-motion:reduce){*,*::before,*::after{transition:none!important}}
  `;
  document.head.appendChild(style);
  const box=()=>document.getElementById('hud-screen-content');
  function showImage(screen){
    const container=box();if(!container||!screen?.image_url)return;
    const root=document.createElement('div');root.className='peter-image-view';
    const title=document.createElement('h3');title.textContent=screen.title||'Immagine';
    const body=document.createElement('div');body.className='peter-image-body';
    const img=document.createElement('img');img.src=screen.image_url;img.alt=screen.title||'Immagine trovata';
    const info=document.createElement('div');info.className='peter-image-info';info.textContent=screen.content||'Immagine trovata sul web.';
    if(screen.source_url){const link=document.createElement('a');link.href=screen.source_url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='Apri fonte ↗';info.append(document.createElement('br'),link);}
    img.addEventListener('error',()=>{info.textContent='Immagine non accessibile direttamente; prova un’altra ricerca.'},{once:true});
    body.append(img,info);root.append(title,body);container.replaceChildren(root);
    const badge=document.getElementById('hud-status-badge');if(badge)badge.textContent='ACTIVE // IMAGE';
  }
  const original=window.updateHudScreen;
  if(typeof original==='function')window.updateHudScreen=screen=>{if(screen?.type==='IMAGE_PREVIEW'&&screen.image_url){showImage(screen);return;}return original(screen);};

  // Image intent goes through the normal /chat reasoning pipeline and the image
  // lookup concurrently; this avoids the previous duplicate chat request.
  const input=document.getElementById('cmd-input'),send=document.getElementById('send-cmd-btn');let busy=false;
  const imageIntent=text=>/\b(immagin(?:e|i)|foto|fotografie)\b/i.test(text)&&/\b(mostra(?:mi)?|cerca|trova|fammi vedere|voglio)\b/i.test(text);
  async function sendImageRequest(event){
    if(!input||!imageIntent(input.value.trim())||busy)return;
    event.preventDefault();event.stopImmediatePropagation();busy=true;if(send)send.disabled=true;
    const message=input.value.trim();input.value='';
    const feed=document.getElementById('chat-feed');
    const append=(text,kind='peter')=>{if(!feed)return;const el=document.createElement('div');el.className=`msg ${kind}`;el.textContent=String(text);feed.append(el);feed.scrollTop=feed.scrollHeight;};
    append(message,'user');const form=new FormData();form.append('message',message);
    try{
      const chatPromise=fetch('/chat',{method:'POST',body:form});
      const imagePromise=fetch('/api/images/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:message})}).then(async r=>({ok:r.ok,data:await r.json()}));
      const [chatResponse,imageResult]=await Promise.all([chatPromise,imagePromise]);const chat=await chatResponse.json();
      if(!chatResponse.ok)throw new Error(chat.detail||'Richiesta non riuscita');
      append(chat.reply||'Risposta vuota');if(chat.reasoning){const r=document.getElementById('reasoning-preview');if(r)r.textContent=chat.reasoning;}
      if(imageResult.ok)showImage({type:'IMAGE_PREVIEW',...imageResult.data});else if(chat.screen&&typeof window.updateHudScreen==='function')window.updateHudScreen(chat.screen);
    }catch(error){append(`Errore: ${error.message}`,'system');}
    finally{busy=false;if(send)send.disabled=false;input.focus();}
  }
  if(send)send.addEventListener('click',sendImageRequest,true);
  if(input)input.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey&&imageIntent(input.value.trim()))sendImageRequest(event);},true);

  const graph=document.getElementById('view-nexus');
  if(graph){const heading=graph.querySelector('.view-heading');if(heading){
    const chips=document.createElement('div');chips.className='brain-status';
    for(const [label,id] of [['NODI','node-count'],['CONNESSIONI','edge-count']]){const chip=document.createElement('span');chip.className='brain-chip';chip.textContent=`${label} · `;const value=document.createElement('b');value.id=`brain-${id}`;value.textContent='0';chip.append(value);chips.append(chip);}
    const syncChip=document.createElement('span');syncChip.className='brain-chip';syncChip.id='brain-sync-chip';syncChip.textContent='SUPABASE · LIVE';chips.append(syncChip);heading.append(chips);
    const sync=document.getElementById('graph-status');if(sync)new MutationObserver(()=>{syncChip.textContent=`SUPABASE · ${sync.textContent||'LIVE'}`;}).observe(sync,{childList:true,subtree:true,characterData:true});
    const updateCounts=()=>{for(const id of ['node-count','edge-count']){const source=document.getElementById(id),target=document.getElementById(`brain-${id}`);if(source&&target)target.textContent=source.textContent;}};
    updateCounts();setInterval(updateCounts,1000);
  }}
})();
