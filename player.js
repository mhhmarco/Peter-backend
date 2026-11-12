/* Peter HUD YouTube player: official IFrame API, autoplay when the browser permits. */
(() => {
  'use strict';
  const API_URL = 'https://www.youtube.com/iframe_api';
  const STYLE_ID = 'peter-media-player-styles';
  let apiPromise = null, player = null, playerCounter = 0, requestCounter = 0, progressTimer = null;
  let originalUpdateHudScreen = null;

  function loadYouTubeApi() {
    if (window.YT?.Player) return Promise.resolve(window.YT);
    if (apiPromise) return apiPromise;
    apiPromise = new Promise((resolve, reject) => {
      const previousCallback = window.onYouTubeIframeAPIReady;
      const timeoutId = window.setTimeout(() => reject(new Error('Timeout caricamento YouTube Player API')), 15000);
      window.onYouTubeIframeAPIReady = () => {
        window.clearTimeout(timeoutId);
        try { previousCallback?.(); } catch (error) { console.warn(error); }
        window.YT?.Player ? resolve(window.YT) : reject(new Error('YouTube Player API non inizializzata'));
      };
      let script = document.querySelector('script[src*="youtube.com/iframe_api"]');
      if (!script) {
        script = document.createElement('script'); script.src = API_URL; script.async = true;
        script.onerror = () => { window.clearTimeout(timeoutId); reject(new Error('Impossibile caricare YouTube Player API')); };
        document.head.appendChild(script);
      }
    });
    return apiPromise;
  }

  function extractVideoId(value) {
    if (!value) return null;
    try {
      const url = new URL(value, location.href);
      const host = url.hostname.toLowerCase().replace(/^www\./, '');
      let id = host === 'youtu.be' ? url.pathname.split('/').filter(Boolean)[0] : null;
      if (!id && ['youtube.com','m.youtube.com','music.youtube.com','youtube-nocookie.com'].includes(host)) {
        id = url.searchParams.get('v') || url.pathname.match(/^\/(?:embed|shorts|live|v)\/([^/?]+)/)?.[1];
      }
      return id && /^[A-Za-z0-9_-]{11}$/.test(id) ? id : null;
    } catch (_) { return null; }
  }
  const isYouTubeMedia = s => s?.type === 'MEDIA_PLAYER' &&
    Boolean(s.video_id || extractVideoId(s.embed_url) || extractVideoId(s.watch_url) || String(s.source || '').toLowerCase().includes('youtube'));

  function installStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style'); style.id = STYLE_ID;
    style.textContent = `
      .peter-player{width:100%;height:100%;min-height:0;display:flex;flex-direction:column;gap:8px;color:#f8fafc;font:13px/1.4 system-ui,-apple-system,sans-serif}
      .peter-player-title{color:#eafaff;font-weight:650;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:0 0 auto;font-size:14px}
      .peter-player-frame{position:relative;flex:1 1 auto;min-height:210px;width:100%;aspect-ratio:16/9;background:#000;border:1px solid rgba(255,255,255,.15);border-radius:16px;overflow:hidden;box-shadow:0 14px 36px rgba(0,0,0,.32)}
      .peter-player-mount,.peter-player-mount iframe{position:absolute;inset:0;width:100%!important;height:100%!important;border:0}
      .peter-player-status{min-height:16px;max-height:34px;overflow:auto;color:#aab8ca;font-size:11px;flex:0 0 auto}
      .peter-player-controls{display:flex;align-items:center;gap:7px;flex-wrap:wrap;flex:0 0 auto}
      .peter-player-controls button,.peter-player-controls a{color:#f8fafc;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);border-radius:999px;padding:7px 11px;font-size:11px;cursor:pointer;text-decoration:none;backdrop-filter:blur(14px)}
      .peter-player-controls button:hover,.peter-player-controls a:hover{background:rgba(255,255,255,.15);border-color:rgba(255,255,255,.3)}
      .peter-player-controls button:disabled{opacity:.45;cursor:not-allowed}.peter-player-seek{flex:1 1 100px;min-width:80px;accent-color:#91dcff}
      .peter-player-volume{width:65px;accent-color:#91dcff}.peter-player-time{min-width:64px;color:#cbd5e1;font:10px ui-monospace,monospace;text-align:center}
      @media(max-width:600px){.peter-player-frame{min-height:180px}.peter-player-controls{gap:4px}.peter-player-controls button,.peter-player-controls a{padding:6px 9px}}
    `;
    document.head.appendChild(style);
  }
  function stopProgressTimer() { if (progressTimer !== null) clearInterval(progressTimer); progressTimer = null; }
  function destroyPlayer() { stopProgressTimer(); try { player?.destroy?.(); } catch (_) {} player = null; }
  function formatTime(seconds) { if (!Number.isFinite(seconds) || seconds < 0) return '0:00'; const n=Math.floor(seconds); return `${Math.floor(n/60)}:${String(n%60).padStart(2,'0')}`; }
  function button(text,title,action){const b=document.createElement('button');b.type='button';b.textContent=text;b.title=title;b.addEventListener('click',action);return b;}
  function externalLink(text,href){const a=document.createElement('a');a.textContent=text;a.href=href;a.target='_blank';a.rel='noopener noreferrer';return a;}

  function render(screen) {
    const requestId=++requestCounter; destroyPlayer(); installStyles();
    const container=document.getElementById('hud-screen-content'), badge=document.getElementById('hud-status-badge');
    if(!container)return; if(badge)badge.textContent='ACTIVE // MEDIA_PLAYER';
    const title=screen.title||'YouTube';
    const videoId=screen.video_id||extractVideoId(screen.embed_url)||extractVideoId(screen.watch_url);
    const watchUrl=videoId?`https://www.youtube.com/watch?v=${encodeURIComponent(videoId)}`:(screen.watch_url||`https://www.youtube.com/results?search_query=${encodeURIComponent(title)}`);
    const root=document.createElement('div');root.className='peter-player';
    const heading=document.createElement('div');heading.className='peter-player-title';heading.textContent=title;heading.title=title;
    const frame=document.createElement('div');frame.className='peter-player-frame';
    const mount=document.createElement('div');mount.className='peter-player-mount';mount.id=`peter-youtube-player-${++playerCounter}`;frame.append(mount);
    const status=document.createElement('div');status.className='peter-player-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');
    const controls=document.createElement('div');controls.className='peter-player-controls';
    const playPause=button('▶','Riproduci o metti in pausa',()=>{if(!player)return;const state=player.getPlayerState();if(state===window.YT.PlayerState.PLAYING||state===window.YT.PlayerState.BUFFERING)player.pauseVideo();else{player.unMute();player.playVideo();}});playPause.disabled=true;
    const stop=button('■','Ferma',()=>player?.stopVideo());stop.disabled=true;
    const currentTime=document.createElement('span');currentTime.className='peter-player-time';currentTime.textContent='0:00 / 0:00';
    const seek=document.createElement('input');seek.className='peter-player-seek';seek.type='range';seek.min='0';seek.max='1000';seek.value='0';seek.setAttribute('aria-label','Posizione del video');seek.disabled=true;
    seek.addEventListener('change',()=>{const duration=player?.getDuration?.()||0;if(duration>0)player.seekTo(Number(seek.value)/1000*duration,true);});
    const mute=button('🔊','Attiva o disattiva audio',()=>{if(!player)return;if(player.isMuted()){player.unMute();mute.textContent='🔊';}else{player.mute();mute.textContent='🔇';}});mute.disabled=true;
    const volume=document.createElement('input');volume.className='peter-player-volume';volume.type='range';volume.min='0';volume.max='100';volume.value='75';volume.setAttribute('aria-label','Volume');volume.disabled=true;volume.addEventListener('input',()=>player?.setVolume(Number(volume.value)));
    controls.append(playPause,stop,currentTime,seek,mute,volume,externalLink('Apri su YouTube ↗',watchUrl));
    root.append(heading,frame,status,controls);container.replaceChildren(root);
    if(!videoId){status.textContent='Nessun video riproducibile trovato. Apri i risultati su YouTube.';return;}
    status.textContent='Caricamento player YouTube…';
    loadYouTubeApi().then(YT=>{
      if(requestId!==requestCounter||!document.getElementById(mount.id))return;
      player=new YT.Player(mount.id,{width:'100%',height:'100%',videoId,host:'https://www.youtube-nocookie.com',playerVars:{autoplay:1,controls:1,playsinline:1,rel:0,enablejsapi:1,origin:location.origin},events:{
        onReady:()=>{if(requestId!==requestCounter)return;playPause.disabled=stop.disabled=mute.disabled=volume.disabled=seek.disabled=false;player.setVolume(Number(volume.value));
          // Attempt audible autoplay first. If blocked, retry muted; browsers may
          // prohibit audible autoplay, so the visible unmute/play control remains available.
          status.textContent='Avvio automatico…';player.playVideo();
          window.setTimeout(()=>{if(requestId!==requestCounter)return;const state=player?.getPlayerState?.();if(state!==YT.PlayerState.PLAYING){player?.mute?.();player?.playVideo?.();status.textContent='Avvio automatico senza audio: tocca 🔊 per attivarlo.';}},700);
          stopProgressTimer();progressTimer=window.setInterval(()=>{if(!player||requestId!==requestCounter)return;const duration=player.getDuration()||0,time=player.getCurrentTime()||0;currentTime.textContent=`${formatTime(time)} / ${formatTime(duration)}`;if(duration>0&&document.activeElement!==seek)seek.value=String(Math.round(time/duration*1000));},500);
        },
        onStateChange:event=>{if(requestId!==requestCounter)return;if(event.data===YT.PlayerState.PLAYING){playPause.textContent='Ⅱ';status.textContent=player.isMuted()?'In riproduzione senza audio · premi 🔊':'In riproduzione';}else if(event.data===YT.PlayerState.PAUSED||event.data===YT.PlayerState.ENDED){playPause.textContent='▶';status.textContent=event.data===YT.PlayerState.ENDED?'Video terminato':'In pausa';}else if(event.data===YT.PlayerState.BUFFERING)status.textContent='Caricamento video…';},
        onError:event=>{if(requestId!==requestCounter)return;const errors={2:'ID video non valido.',5:'Player HTML5 non riuscito.',100:'Video non disponibile.',101:'Il proprietario non consente l’embed.',150:'Il proprietario non consente l’embed.',153:'Referrer non valido: apri il dominio HTTPS pubblico.'};status.textContent=`${errors[event.data]||`Errore YouTube ${event.data}.`} Apri il video su YouTube o prova un altro risultato.`;frame.style.borderColor='#ef4444';controls.append(externalLink('Cerca un altro video ↗',`https://www.youtube.com/results?search_query=${encodeURIComponent(title)}`));}
      }});
    }).catch(error=>{if(requestId===requestCounter)status.textContent=`${error.message}. Usa “Apri su YouTube”.`;});
  }
  function handleScreen(screen){if(!screen)return;if(isYouTubeMedia(screen)){render(screen);return;}destroyPlayer();if(typeof originalUpdateHudScreen==='function')originalUpdateHudScreen(screen);}
  function installHook(){if(typeof window.updateHudScreen!=='function'){setTimeout(installHook,0);return;}originalUpdateHudScreen=window.updateHudScreen;window.updateHudScreen=handleScreen;}
  installHook();
})();
