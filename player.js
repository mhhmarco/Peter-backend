/* YouTube playback enhancement for Peter HUD.
 * Uses YouTube's official IFrame Player API. Playback is intentionally started
 * only after a click because browsers block autoplay without a user gesture.
 */
(() => {
  const apiUrl = "https://www.youtube.com/iframe_api";
  let player = null;
  let playerCounter = 0;
  let currentScreen = null;
  let apiPromise = null;

  function loadYouTubeApi() {
    if (window.YT && window.YT.Player) return Promise.resolve(window.YT);
    if (apiPromise) return apiPromise;

    apiPromise = new Promise((resolve, reject) => {
      const previousCallback = window.onYouTubeIframeAPIReady;
      const timeout = window.setTimeout(
        () => reject(new Error("Timeout caricamento YouTube Player API")),
        15000
      );

      window.onYouTubeIframeAPIReady = () => {
        window.clearTimeout(timeout);
        if (typeof previousCallback === "function") previousCallback();
        resolve(window.YT);
      };

      let script = document.querySelector(`script[src^="${apiUrl}"]`);
      if (!script) {
        script = document.createElement("script");
        script.src = apiUrl;
        script.async = true;
        script.onerror = () => {
          window.clearTimeout(timeout);
          reject(new Error("Impossibile caricare YouTube Player API"));
        };
        document.head.appendChild(script);
      }
    });

    return apiPromise;
  }

  function videoIdFromUrl(value) {
    if (!value) return null;
    try {
      const url = new URL(value, window.location.href);
      const host = url.hostname.replace(/^www\./, "");
      let id = null;
      if (host === "youtu.be") id = url.pathname.split("/").filter(Boolean)[0];
      else if (host.endsWith("youtube.com") || host.endsWith("youtube-nocookie.com")) {
        id = url.searchParams.get("v");
        if (!id) id = url.pathname.match(/^\/(?:embed|shorts|live)\/([^/?]+)/)?.[1];
      }
      return id && /^[A-Za-z0-9_-]{11}$/.test(id) ? id : null;
    } catch (_) {
      return null;
    }
  }

  function makeButton(label, className, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.className = className;
    button.addEventListener("click", onClick);
    return button;
  }

  function makeLink(label, href) {
    const link = document.createElement("a");
    link.textContent = label;
    link.href = href;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.className = "peter-player-link";
    return link;
  }

  function youtubeSearchUrl(title) {
    return `https://www.youtube.com/results?search_query=${encodeURIComponent(title || "")}`;
  }

  function destroyPlayer() {
    if (player && typeof player.destroy === "function") {
      try { player.destroy(); } catch (_) {}
    }
    player = null;
  }

  function showMediaPlayer(screen) {
    currentScreen = screen;
    destroyPlayer();

    const container = document.getElementById("hud-screen-content");
    const badge = document.getElementById("hud-status-badge");
    if (!container) return;
    if (badge) badge.textContent = "ACTIVE // MEDIA_PLAYER";

    const title = screen.title || "YouTube";
    const videoId = screen.video_id || videoIdFromUrl(screen.embed_url) || videoIdFromUrl(screen.watch_url);
    const watchUrl = screen.watch_url && screen.watch_url.startsWith("https://www.youtube.com/")
      ? screen.watch_url
      : videoId ? `https://www.youtube.com/watch?v=${videoId}` : youtubeSearchUrl(title);

    const root = document.createElement("div");
    root.className = "peter-player";
    root.style.cssText = "width:min(100%,760px);max-height:100%;display:flex;flex-direction:column;gap:8px;color:#f8fafc;font:13px system-ui,sans-serif;";

    const heading = document.createElement("div");
    heading.textContent = title;
    heading.title = title;
    heading.style.cssText = "overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#00f0ff;font-weight:700;";

    const frame = document.createElement("div");
    frame.style.cssText = "position:relative;width:100%;aspect-ratio:16/9;max-height:calc(100% - 60px);min-height:120px;background:#000;border:1px solid #00f0ff;border-radius:12px;overflow:hidden;";

    const playerMount = document.createElement("div");
    playerMount.id = `peter-youtube-player-${++playerCounter}`;
    playerMount.style.cssText = "position:absolute;inset:0;width:100%;height:100%;";
    frame.appendChild(playerMount);

    const status = document.createElement("div");
    status.setAttribute("role", "status");
    status.style.cssText = "min-height:18px;color:#94a3b8;font-size:12px;";
    status.textContent = videoId ? "Player pronto. Premi Riproduci; alcuni video non consentono la riproduzione incorporata." : "Non ho ricevuto un ID video riproducibile.";

    const controls = document.createElement("div");
    controls.style.cssText = "display:flex;align-items:center;gap:8px;flex-wrap:wrap;";

    const playButton = makeButton("▶ Riproduci", "cmd-btn", () => {
      if (player) {
        player.playVideo();
        status.textContent = "Avvio riproduzione…";
      }
    });
    playButton.style.cssText = "padding:8px 14px;border:0;border-radius:18px;background:linear-gradient(135deg,#00f0ff,#8b5cf6);font-weight:700;cursor:pointer;";
    controls.append(playButton, makeLink("Apri su YouTube ↗", watchUrl));

    if (!videoId) {
      const searchLink = makeLink("Cerca un video su YouTube ↗", youtubeSearchUrl(title));
      controls.appendChild(searchLink);
    }

    root.append(heading, frame, status, controls);
    container.replaceChildren(root);

    if (!videoId) return;

    loadYouTubeApi().then((YT) => {
      // A newer request may have replaced this player while the API was loading.
      if (currentScreen !== screen || !document.getElementById(playerMount.id)) return;

      player = new YT.Player(playerMount.id, {
        width: "100%",
        height: "100%",
        videoId,
        host: "https://www.youtube-nocookie.com",
        playerVars: {
          autoplay: 0,
          controls: 1,
          playsinline: 1,
          rel: 0,
          enablejsapi: 1,
          origin: window.location.origin,
        },
        events: {
          onReady: () => { status.textContent = "Pronto. Premi Riproduci o usa i controlli del video."; },
          onStateChange: (event) => {
            if (event.data === YT.PlayerState.PLAYING) status.textContent = "In riproduzione";
            else if (event.data === YT.PlayerState.PAUSED) status.textContent = "In pausa";
            else if (event.data === YT.PlayerState.ENDED) status.textContent = "Video terminato";
            else if (event.data === YT.PlayerState.BUFFERING) status.textContent = "Caricamento video…";
          },
          onError: (event) => {
            const explanations = {
              2: "ID video non valido.",
              5: "Il player HTML5 non è riuscito a riprodurre questo video.",
              100: "Video rimosso, privato o non disponibile.",
              101: "Il proprietario del video non consente la riproduzione incorporata.",
              150: "Il proprietario del video non consente la riproduzione incorporata.",
              153: "YouTube non ha ricevuto un'identità/referrer valido per questo player.",
            };
            status.textContent = `${explanations[event.data] || `Errore YouTube ${event.data}.`} Usa “Apri su YouTube” o cerca un altro risultato.`;
            frame.style.borderColor = "#ef4444";
          },
        },
      });
    }).catch((error) => {
      status.textContent = `${error.message}. Puoi aprire il video direttamente su YouTube.`;
    });
  }

  const previousUpdateHudScreen = window.updateHudScreen;
  window.updateHudScreen = function (screen) {
    if (screen && screen.type === "MEDIA_PLAYER") {
      showMediaPlayer(screen);
      return;
    }
    if (typeof previousUpdateHudScreen === "function") previousUpdateHudScreen(screen);
  };
})();
