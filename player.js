/* Peter HUD YouTube player: explicit playback controls and resilient HUD integration. */
(() => {
  'use strict';
  const API_URL = 'https://www.youtube.com/iframe_api';
  let apiPromise;
  let player;
  let requestId = 0;
  let progressTimer;
  let originalUpdate;

  function loadApi() {
    if (window.YT?.Player) return Promise.resolve(window.YT);
    if (apiPromise) return apiPromise;
    apiPromise = new Promise((resolve, reject) => {
      const previous = window.onYouTubeIframeAPIReady;
      const timeout = setTimeout(() => reject(new Error('Timeout caricamento YouTube Player API')), 15000);
      window.onYouTubeIframeAPIReady = () => {
        clearTimeout(timeout);
        try { previous?.(); } catch (error) { console.warn(error); }
        window.YT?.Player ? resolve(window.YT) : reject(new Error('YouTube Player API non inizializzata'));
      };
      let script = document.querySelector('script[src*="youtube.com/iframe_api"]');
      if (!script) {
        script = document.createElement('script');
        script.src = API_URL;
        script.async = true;
        script.onerror = () => { clearTimeout(timeout); reject(new Error('Impossibile caricare YouTube Player API')); };
        document.head.appendChild(script);
      }
    });
    return apiPromise;
  }

  function videoIdFrom(value) {
    if (!value) return null;
    try {
      const url = new URL(value, location.href);
      const host = url.hostname.toLowerCase().replace(/^www\./, '');
      let id = host === 'youtu.be' ? url.pathname.split('/').filter(Boolean)[0] : null;
      if (!id && ['youtube.com', 'm.youtube.com', 'music.youtube.com', 'youtube-nocookie.com'].includes(host)) {
        id = url.searchParams.get('v') || url.pathname.match(/^\/(?:embed|shorts|live|v)\/([^/?]+)/)?.[1];
      }
      return id && /^[A-Za-z0-9_-]{11}$/.test(id) ? id : null;
    } catch (_) { return null; }
  }

  function cleanup() {
    if (progressTimer) clearInterval(progressTimer);
    progressTimer = null;
    try { player?.destroy?.(); } catch (_) {}
    player = null;
  }

  function show(screen) {
    const thisRequest = ++requestId;
    cleanup();
    const content = document.getElementById('hud-screen-content');
    const badge = document.getElementById('hud-status-badge');
    if (!content) return;
    if (badge) badge.textContent = 'ACTIVE // MEDIA_PLAYER';

    const id = screen.video_id || videoIdFrom(screen.embed_url) || videoIdFrom(screen.watch_url);
    const title = screen.title || 'YouTube';
    const root = document.createElement('div');
    root.className = 'peter-player';
    root.style.cssText = 'height:100%;min-height:0;display:flex;flex-direction:column;gap:8px;color:#eef6ff;font:13px system-ui,sans-serif';
    const heading = document.createElement('strong');
    heading.textContent = title;
    heading.style.cssText = 'overflow:hidden;text-overflow:ellipsis;white-space:nowrap';
    const frame = document.createElement('div');
    frame.style.cssText = 'position:relative;flex:1;min-height:220px;background:#000;border-radius:12px;overflow:hidden';
    const mount = document.createElement('div');
    mount.id = `peter-yt-${Date.now()}-${thisRequest}`;
    frame.append(mount);
    const status = document.createElement('div');
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    status.textContent = id ? 'Caricamento player…' : 'Nessun video riproducibile trovato.';
    const controls = document.createElement('div');
    controls.style.cssText = 'display:flex;align-items:center;gap:8px;flex-wrap:wrap';
    const play = document.createElement('button');
    play.type = 'button'; play.textContent = '▶ Riproduci'; play.disabled = true;
    play.onclick = () => {
      if (!player) return;
      const playing = player.getPlayerState?.() === window.YT?.PlayerState?.PLAYING;
      if (playing) { player.pauseVideo(); play.textContent = '▶ Riprendi'; }
      else { player.unMute(); player.playVideo(); play.textContent = 'Ⅱ Pausa'; }
    };
    const open = document.createElement('a');
    open.textContent = 'Apri su YouTube ↗';
    open.href = id ? `https://www.youtube.com/watch?v=${encodeURIComponent(id)}` : (screen.watch_url || 'https://www.youtube.com/');
    open.target = '_blank'; open.rel = 'noopener noreferrer';
    controls.append(play, open);
    root.append(heading, frame, status, controls);
    content.replaceChildren(root);
    if (!id) return;

    loadApi().then(YT => {
      if (thisRequest !== requestId || !document.getElementById(mount.id)) return;
      player = new YT.Player(mount.id, {
        videoId: id,
        host: 'https://www.youtube-nocookie.com',
        playerVars: { autoplay: 0, controls: 1, playsinline: 1, rel: 0, enablejsapi: 1, origin: location.origin },
        events: {
          onReady: () => {
            if (thisRequest !== requestId) return;
            play.disabled = false;
            status.textContent = 'Pronto. Premi Riproduci per avviare il video (l’autoplay può essere bloccato dal browser).';
          },
          onStateChange: event => {
            if (thisRequest !== requestId) return;
            if (event.data === YT.PlayerState.PLAYING) { play.textContent = 'Ⅱ Pausa'; status.textContent = 'Video in riproduzione.'; }
            else if (event.data === YT.PlayerState.PAUSED) { play.textContent = '▶ Riprendi'; status.textContent = 'Video in pausa.'; }
            else if (event.data === YT.PlayerState.ENDED) { play.textContent = '▶ Riproduci'; status.textContent = 'Video terminato.'; }
          },
          onError: event => {
            if (thisRequest !== requestId) return;
            const messages = { 2: 'ID video non valido.', 5: 'Errore del player HTML5.', 100: 'Video non disponibile.', 101: 'Il proprietario non consente la riproduzione incorporata.', 150: 'Il proprietario non consente la riproduzione incorporata.', 153: 'YouTube richiede un referrer valido: apri la dashboard dal dominio HTTPS pubblico.' };
            status.textContent = `${messages[event.data] || `Errore YouTube ${event.data}.`} Usa “Apri su YouTube”.`;
          },
        },
      });
    }).catch(error => { if (thisRequest === requestId) status.textContent = `${error.message}. Usa “Apri su YouTube”.`; });
  }

  function isYoutube(screen) {
    return screen?.type === 'MEDIA_PLAYER' && (
      String(screen.source || '').toLowerCase().includes('youtube') ||
      Boolean(screen.video_id || videoIdFrom(screen.embed_url) || videoIdFrom(screen.watch_url))
    );
  }
  function hook() {
    if (typeof window.updateHudScreen !== 'function') { setTimeout(hook, 25); return; }
    if (window.updateHudScreen.__peterYoutubeHook) return;
    originalUpdate = window.updateHudScreen;
    const wrapped = screen => {
      if (isYoutube(screen)) return show(screen);
      cleanup();
      return originalUpdate(screen);
    };
    wrapped.__peterYoutubeHook = true;
    window.updateHudScreen = wrapped;
  }
  hook();
})();
