/* Peter HUD YouTube player.
 * Uses YouTube's official IFrame Player API (same approach as lightweight
 * wrappers such as https://github.com/feross/yt-player). No npm build step is
 * needed, so this works with the existing FastAPI/Render deployment.
 * Playback begins only after a user action; browsers commonly block autoplay.
 */
(() => {
  "use strict";

  const API_URL = "https://www.youtube.com/iframe_api";
  const STYLE_ID = "peter-media-player-styles";
  let apiPromise = null;
  let player = null;
  let playerCounter = 0;
  let requestCounter = 0;
  let progressTimer = null;
  let activeKind = null;
  let originalUpdateHudScreen = null;

  function loadYouTubeApi() {
    if (window.YT && window.YT.Player) return Promise.resolve(window.YT);
    if (apiPromise) return apiPromise;

    apiPromise = new Promise((resolve, reject) => {
      const previousCallback = window.onYouTubeIframeAPIReady;
      const timeoutId = window.setTimeout(() => {
        reject(new Error("Timeout caricamento YouTube Player API"));
      }, 20000);

      window.onYouTubeIframeAPIReady = () => {
        window.clearTimeout(timeoutId);
        if (typeof previousCallback === "function") {
          try { previousCallback(); } catch (error) { console.warn(error); }
        }
        if (window.YT && window.YT.Player) resolve(window.YT);
        else reject(new Error("YouTube Player API non inizializzata"));
      };

      let script = document.querySelector('script[src*="youtube.com/iframe_api"]');
      if (!script) {
        script = document.createElement("script");
        script.src = API_URL;
        script.async = true;
        script.onerror = () => {
          window.clearTimeout(timeoutId);
          reject(new Error("Impossibile caricare YouTube Player API"));
        };
        document.head.appendChild(script);
      }
    });

    return apiPromise;
  }

  function extractVideoId(value) {
    if (!value) return null;
    try {
      const url = new URL(value, window.location.href);
      const host = url.hostname.toLowerCase().replace(/^www\./, "");
      let id = null;
      if (host === "youtu.be") {
        id = url.pathname.split("/").filter(Boolean)[0];
      } else if (host === "youtube.com" || host === "youtube-nocookie.com" || host.endsWith(".youtube.com")) {
        id = url.searchParams.get("v");
        if (!id) id = url.pathname.match(/^\/(?:embed|shorts|live|v)\/([^/?]+)/)?.[1];
      }
      return id && /^[A-Za-z0-9_-]{11}$/.test(id) ? id : null;
    } catch (_) {
      return null;
    }
  }

  function isYouTubeMedia(screen) {
    if (!screen || screen.type !== "MEDIA_PLAYER") return false;
    const values = [screen.source, screen.embed_url, screen.watch_url].filter(Boolean).join(" ").toLowerCase();
    return Boolean(screen.video_id || extractVideoId(screen.embed_url) || extractVideoId(screen.watch_url) || values.includes("youtube"));
  }

  function installStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
      .peter-player { width:min(100%,760px); height:100%; min-height:0; display:flex; flex-direction:column; gap:7px; color:#f8fafc; font:12px/1.35 system-ui,-apple-system,sans-serif; }
      .peter-player-title { color:#00f0ff; font-weight:700; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:0 0 auto; }
      .peter-player-frame { position:relative; flex:1 1 auto; min-height:80px; width:100%; background:#000; border:1px solid #00f0ff; border-radius:12px; overflow:hidden; }
      .peter-player-mount, .peter-player-mount iframe { position:absolute; inset:0; width:100% !important; height:100% !important; border:0; }
      .peter-player-status { min-height:16px; max-height:32px; overflow:auto; color:#94a3b8; font-size:11px; flex:0 0 auto; }
      .peter-player-controls { display:flex; align-items:center; gap:6px; flex-wrap:wrap; flex:0 0 auto; }
      .peter-player-controls button, .peter-player-controls a { color:#f8fafc; background:#0f172a; border:1px solid rgba(0,240,255,.35); border-radius:8px; padding:5px 9px; font-size:11px; cursor:pointer; text-decoration:none; }
      .peter-player-controls button:hover, .peter-player-controls a:hover { border-color:#00f0ff; color:#00f0ff; }
      .peter-player-controls button:disabled { opacity:.45; cursor:not-allowed; }
      .peter-player-seek { flex:1 1 100px; min-width:90px; accent-color:#00f0ff; }
      .peter-player-volume { width:64px; accent-color:#00f0ff; }
      .peter-player-time { min-width:62px; color:#cbd5e1; font:10px ui-monospace,monospace; text-align:center; }
      @media(max-width:600px) { .peter-player-controls { gap:4px; } .peter-player-controls button,.peter-player-controls a { padding:5px 7px; } }
    `;
    document.head.appendChild(style);
  }

  function stopProgressTimer() {
    if (progressTimer !== null) window.clearInterval(progressTimer);
    progressTimer = null;
  }

  function destroyPlayer() {
    stopProgressTimer();
    if (player && typeof player.destroy === "function") {
      try { player.destroy(); } catch (_) {}
    }
    player = null;
  }

  function formatTime(seconds) {
    if (!Number.isFinite(seconds) || seconds < 0) return "0:00";
    const whole = Math.floor(seconds);
    const minutes = Math.floor(whole / 60);
    return `${minutes}:${String(whole % 60).padStart(2, "0")}`;
  }

  function makeButton(text, title, action) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = text;
    button.title = title;
    button.addEventListener("click", action);
    return button;
  }

  function makeExternalLink(text, href) {
    const link = document.createElement("a");
    link.textContent = text;
    link.href = href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    return link;
  }

  function render(screen) {
    const requestId = ++requestCounter;
    activeKind = "youtube";
    destroyPlayer();
    installStyles();

    const container = document.getElementById("hud-screen-content");
    const badge = document.getElementById("hud-status-badge");
    if (!container) return;
    if (badge) badge.textContent = "ACTIVE // MEDIA_PLAYER";

    const title = screen.title || "YouTube";
    const videoId = screen.video_id || extractVideoId(screen.embed_url) || extractVideoId(screen.watch_url);
    const watchUrl = videoId
      ? `https://www.youtube.com/watch?v=${encodeURIComponent(videoId)}`
      : (screen.watch_url || `https://www.youtube.com/results?search_query=${encodeURIComponent(title)}`);

    const root = document.createElement("div");
    root.className = "peter-player";
    const heading = document.createElement("div");
    heading.className = "peter-player-title";
    heading.textContent = title;
    heading.title = title;

    const frame = document.createElement("div");
    frame.className = "peter-player-frame";
    const mount = document.createElement("div");
    mount.className = "peter-player-mount";
    mount.id = `peter-youtube-player-${++playerCounter}`;
    frame.appendChild(mount);

    const status = document.createElement("div");
    status.className = "peter-player-status";
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");

    const controls = document.createElement("div");
    controls.className = "peter-player-controls";
    const playPause = makeButton("▶", "Riproduci", () => {
      if (!player) return;
      const state = player.getPlayerState();
      if (state === window.YT.PlayerState.PLAYING || state === window.YT.PlayerState.BUFFERING) {
        player.pauseVideo();
      } else {
        player.playVideo();
      }
    });
    playPause.disabled = true;

    const stop = makeButton("■", "Ferma", () => {
      if (player) player.stopVideo();
    });
    stop.disabled = true;

    const currentTime = document.createElement("span");
    currentTime.className = "peter-player-time";
    currentTime.textContent = "0:00 / 0:00";

    const seek = document.createElement("input");
    seek.className = "peter-player-seek";
    seek.type = "range";
    seek.min = "0";
    seek.max = "1000";
    seek.value = "0";
    seek.step = "1";
    seek.setAttribute("aria-label", "Posizione del video");
    seek.disabled = true;
    seek.addEventListener("change", () => {
      if (!player) return;
      const duration = player.getDuration();
      if (duration > 0) player.seekTo((Number(seek.value) / 1000) * duration, true);
    });

    const mute = makeButton("🔊", "Disattiva audio", () => {
      if (!player) return;
      if (player.isMuted()) {
        player.unMute();
        mute.textContent = "🔊";
        mute.title = "Disattiva audio";
      } else {
        player.mute();
        mute.textContent = "🔇";
        mute.title = "Attiva audio";
      }
    });
    mute.disabled = true;

    const volume = document.createElement("input");
    volume.className = "peter-player-volume";
    volume.type = "range";
    volume.min = "0";
    volume.max = "100";
    volume.value = "75";
    volume.setAttribute("aria-label", "Volume");
    volume.disabled = true;
    volume.addEventListener("input", () => {
      if (player) player.setVolume(Number(volume.value));
    });

    controls.append(
      playPause,
      stop,
      currentTime,
      seek,
      mute,
      volume,
      makeExternalLink("Apri su YouTube ↗", watchUrl)
    );
    root.append(heading, frame, status, controls);
    container.replaceChildren(root);

    if (!videoId) {
      status.textContent = "Nessun ID video valido ricevuto. Apri YouTube e scegli un video.";
      return;
    }

    status.textContent = "Caricamento player YouTube…";
    loadYouTubeApi().then((YT) => {
      if (requestId !== requestCounter || !document.getElementById(mount.id)) return;

      player = new YT.Player(mount.id, {
        width: "100%",
        height: "100%",
        videoId,
        host: "https://www.youtube-nocookie.com",
        playerVars: {
          autoplay: 0,
          controls: 0,
          playsinline: 1,
          rel: 0,
          enablejsapi: 1,
          origin: window.location.origin,
        },
        events: {
          onReady: () => {
            if (requestId !== requestCounter) return;
            status.textContent = "Pronto. Premi ▶ per avviare; puoi anche usare i controlli qui sotto.";
            playPause.disabled = false;
            stop.disabled = false;
            mute.disabled = false;
            volume.disabled = false;
            seek.disabled = false;
            player.setVolume(Number(volume.value));
            stopProgressTimer();
            progressTimer = window.setInterval(() => {
              if (!player || requestId !== requestCounter) return;
              const duration = player.getDuration() || 0;
              const time = player.getCurrentTime() || 0;
              currentTime.textContent = `${formatTime(time)} / ${formatTime(duration)}`;
              if (duration > 0 && document.activeElement !== seek) {
                seek.value = String(Math.round((time / duration) * 1000));
              }
            }, 500);
          },
          onStateChange: (event) => {
            if (requestId !== requestCounter) return;
            if (event.data === YT.PlayerState.PLAYING) {
              playPause.textContent = "Ⅱ";
              playPause.title = "Pausa";
              status.textContent = "In riproduzione";
            } else if (event.data === YT.PlayerState.PAUSED) {
              playPause.textContent = "▶";
              playPause.title = "Riproduci";
              status.textContent = "In pausa";
            } else if (event.data === YT.PlayerState.ENDED) {
              playPause.textContent = "▶";
              playPause.title = "Riproduci";
              status.textContent = "Video terminato";
            } else if (event.data === YT.PlayerState.BUFFERING) {
              status.textContent = "Caricamento video…";
            } else if (event.data === YT.PlayerState.CUED) {
              status.textContent = "Video caricato. Premi ▶ per avviare.";
            }
          },
          onError: (event) => {
            if (requestId !== requestCounter) return;
            const messages = {
              2: "ID video non valido.",
              5: "Il player HTML5 non è riuscito a riprodurre questo video.",
              100: "Video rimosso, privato o non disponibile.",
              101: "Il proprietario non consente la riproduzione incorporata.",
              150: "Il proprietario non consente la riproduzione incorporata.",
              153: "YouTube non ha ricevuto un referrer valido. Apri la pagina Render con il suo URL HTTPS pubblico.",
            };
            status.textContent = `${messages[event.data] || `Errore YouTube ${event.data}.`} Prova un altro video oppure aprilo su YouTube.`;
            frame.style.borderColor = "#ef4444";
            controls.appendChild(makeExternalLink("Cerca un altro video ↗", `https://www.youtube.com/results?search_query=${encodeURIComponent(title)}`));
          },
        },
      });
    }).catch((error) => {
      if (requestId === requestCounter) {
        status.textContent = `${error.message}. Usa “Apri su YouTube”.`;
      }
    });
  }

  function handleScreen(screen) {
    if (!screen) return;
    if (isYouTubeMedia(screen)) {
      render(screen);
      return;
    }
    activeKind = null;
    destroyPlayer();
    if (typeof originalUpdateHudScreen === "function") originalUpdateHudScreen(screen);
  }

  function installHook() {
    if (typeof window.updateHudScreen !== "function") {
      window.setTimeout(installHook, 0);
      return;
    }
    originalUpdateHudScreen = window.updateHudScreen;
    window.updateHudScreen = handleScreen;
  }

  installHook();
})();
