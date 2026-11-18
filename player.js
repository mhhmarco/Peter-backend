/* Peter HUD YouTube Player — embed diretto resiliente + YouTube IFrame API */
(() => {
  'use strict';
  let requestId = 0;

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
    } catch (_) {
      return null;
    }
  }

  function renderYoutubeEmbed(screen) {
    const thisReq = ++requestId;
    const content = document.getElementById('hud-screen-content');
    const badge = document.getElementById('hud-status-badge');
    if (!content) return;
    if (badge) badge.textContent = 'ACTIVE // YOUTUBE_HUD';

    const id = screen.video_id || videoIdFrom(screen.embed_url) || videoIdFrom(screen.watch_url);
    const title = screen.title || 'YouTube Video';
    const watchUrl = id ? `https://www.youtube.com/watch?v=${encodeURIComponent(id)}` : (screen.watch_url || 'https://www.youtube.com/');

    const root = document.createElement('div');
    root.className = 'peter-player';
    root.style.cssText = 'width:100%;height:100%;display:flex;flex-direction:column;gap:10px;color:#f4f8ff;';

    const header = document.createElement('div');
    header.style.cssText = 'display:flex;align-items:center;justify-content:space-between;gap:8px;';

    const heading = document.createElement('strong');
    heading.textContent = title;
    heading.style.cssText = 'font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;';

    const open = document.createElement('a');
    open.textContent = 'Apri su YouTube ↗';
    open.href = watchUrl;
    open.target = '_blank';
    open.rel = 'noopener noreferrer';
    open.style.cssText = 'color:#7ce8ff;font:600 11px ui-monospace,monospace;text-decoration:none;white-space:nowrap;';

    header.append(heading, open);
    root.append(header);

    if (!id) {
      const empty = document.createElement('div');
      empty.textContent = 'Video non disponibile per la riproduzione diretta.';
      empty.style.cssText = 'padding:18px;border-radius:14px;background:rgba(255,255,255,.04);font-size:12px;color:#a7bad0;';
      root.append(empty);
      content.replaceChildren(root);
      return;
    }

    const frameWrap = document.createElement('div');
    frameWrap.style.cssText = 'position:relative;flex:1 1 auto;min-height:220px;background:#000;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,.14);';

    const iframe = document.createElement('iframe');
    iframe.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?rel=0&modestbranding=1&playsinline=1`;
    iframe.title = title;
    iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
    iframe.allowFullscreen = true;
    iframe.referrerPolicy = 'strict-origin-when-cross-origin';
    iframe.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;border:0;';

    frameWrap.append(iframe);
    root.append(frameWrap);

    if (screen.author) {
      const meta = document.createElement('div');
      meta.textContent = `Canale: ${screen.author}`;
      meta.style.cssText = 'font-size:11px;color:#9ab0c8;';
      root.append(meta);
    }

    if (thisReq === requestId) {
      content.replaceChildren(root);
    }
  }

  function isYoutube(screen) {
    return screen?.type === 'MEDIA_PLAYER' && (
      String(screen.source || '').toLowerCase().includes('youtube') ||
      Boolean(screen.video_id || videoIdFrom(screen.embed_url) || videoIdFrom(screen.watch_url))
    );
  }

  function installHook() {
    if (typeof window.updateHudScreen !== 'function') {
      setTimeout(installHook, 25);
      return;
    }
    if (window.updateHudScreen.__peterYtV11Hook) return;
    const orig = window.updateHudScreen;
    const wrapped = screen => {
      if (isYoutube(screen)) {
        renderYoutubeEmbed(screen);
        return;
      }
      return orig(screen);
    };
    wrapped.__peterYtV11Hook = true;
    window.updateHudScreen = wrapped;
  }

  installHook();
})();
