def get_dashboard_html() -> str:
    return """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PETER COMMAND CENTER v3.0</title>
        <style>
            :root {
                --bg-main: #030712;
                --panel-bg: rgba(10, 20, 38, 0.7);
                --panel-border: rgba(0, 240, 255, 0.18);
                --accent-cyan: #00f0ff;
                --accent-blue: #1d4ed8;
                --accent-green: #10b981;
                --text-bright: #f3f4f6;
                --text-dim: #6b7280;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: "SF Pro Text", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            body { background: var(--bg-main); color: var(--text-bright); height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
            
            /* TOP BAR HUD */
            header { height: 54px; border-bottom: 1px solid var(--panel-border); padding: 0 24px; display: flex; align-items: center; justify-content: space-between; background: rgba(3, 7, 18, 0.95); backdrop-filter: blur(12px); z-index: 100; }
            .header-brand { display: flex; align-items: center; gap: 12px; }
            .logo-icon { width: 28px; height: 28px; border-radius: 50%; border: 2px solid var(--accent-cyan); display: flex; align-items: center; justify-content: center; box-shadow: 0 0 10px var(--accent-cyan); font-size: 11px; font-weight: 800; color: var(--accent-cyan); }
            .header-title { font-size: 14px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; }
            
            .sys-status { display: flex; align-items: center; gap: 8px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); padding: 4px 12px; border-radius: 20px; font-size: 11px; color: var(--accent-green); font-weight: 600; letter-spacing: 1px; }
            .status-dot { width: 6px; height: 6px; background: var(--accent-green); border-radius: 50%; box-shadow: 0 0 8px var(--accent-green); }
            .clock-display { font-family: monospace; font-size: 15px; color: var(--accent-cyan); letter-spacing: 1px; }

            /* MAIN COMMAND CENTER GRID */
            .command-grid { flex: 1; display: grid; grid-template-columns: 240px 1fr 380px; gap: 14px; padding: 14px; height: calc(100vh - 114px); overflow: hidden; }

            /* LEFT SIDEBAR */
            .sidebar-panel { background: var(--panel-bg); border: 1px solid var(--panel-border); border-radius: 14px; padding: 16px; display: flex; flex-direction: column; gap: 16px; backdrop-filter: blur(10px); }
            .nav-menu { display: flex; flex-direction: column; gap: 6px; }
            .nav-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; color: var(--text-dim); text-decoration: none; cursor: pointer; transition: all 0.2s; }
            .nav-item.active, .nav-item:hover { background: rgba(0, 240, 255, 0.08); color: var(--accent-cyan); border-left: 3px solid var(--accent-cyan); }
            
            .voice-widget { margin-top: auto; background: rgba(0, 240, 255, 0.03); border: 1px solid var(--panel-border); border-radius: 12px; padding: 16px; text-align: center; }
            .mic-btn { width: 56px; height: 56px; border-radius: 50%; border: 2px solid var(--accent-cyan); background: rgba(0,240,255,0.1); color: var(--accent-cyan); font-size: 20px; display: flex; align-items: center; justify-content: center; margin: 10px auto; cursor: pointer; box-shadow: 0 0 20px rgba(0,240,255,0.2); transition: all 0.3s; }
            .mic-btn:hover { transform: scale(1.05); box-shadow: 0 0 30px var(--accent-cyan); }

            /* CENTER WORKSPACE */
            .center-workspace { display: grid; grid-template-rows: 240px 1fr; gap: 14px; height: 100%; overflow: hidden; }
            
            /* AI CORE SPHERE CONTAINER */
            .core-visualizer { background: var(--panel-bg); border: 1px solid var(--panel-border); border-radius: 14px; position: relative; display: flex; align-items: center; justify-content: center; overflow: hidden; }
            #core-canvas { width: 100%; height: 100%; position: absolute; top:0; left:0; }
            .core-overlay-text { position: relative; z-index: 2; text-align: center; pointer-events: none; }
            .core-overlay-text h2 { font-size: 22px; font-weight: 900; letter-spacing: 4px; color: #fff; text-shadow: 0 0 16px var(--accent-cyan); }
            .core-overlay-text p { font-size: 11px; font-family: monospace; color: var(--accent-cyan); letter-spacing: 2px; }

            /* LIVE INTELLIGENCE CHAT */
            .feed-panel { background: var(--panel-bg); border: 1px solid var(--panel-border); border-radius: 14px; display: flex; flex-direction: column; overflow: hidden; }
            .panel-header { padding: 12px 16px; border-bottom: 1px solid var(--panel-border); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--accent-cyan); display: flex; justify-content: space-between; align-items: center; }
            
            #chat-feed { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; scroll-behavior: smooth; }
            .msg { max-width: 80%; padding: 10px 14px; border-radius: 12px; font-size: 13px; line-height: 1.5; word-wrap: break-word; }
            .msg.user { align-self: flex-end; background: linear-gradient(135deg, #1d4ed8, #2563eb); color: #fff; border-bottom-right-radius: 2px; }
            .msg.peter { align-self: flex-start; background: rgba(15, 25, 45, 0.9); border: 1px solid var(--panel-border); border-bottom-left-radius: 2px; }
            
            .tool-badge { font-size: 10px; font-family: monospace; color: var(--accent-cyan); background: rgba(0, 240, 255, 0.1); border: 1px solid var(--panel-border); padding: 2px 6px; border-radius: 4px; margin-bottom: 4px; display: inline-block; }
            .media-box { margin-top: 8px; border-radius: 8px; overflow: hidden; border: 1px solid var(--panel-border); background: #000; width: 100%; max-width: 440px; }
            .media-box iframe { width: 100%; height: 210px; border: none; }

            /* RIGHT SIDEBAR - MONITORS */
            .right-sidebar { display: flex; flex-direction: column; gap: 14px; height: 100%; overflow-y: auto; }
            .widget-card { background: var(--panel-bg); border: 1px solid var(--panel-border); border-radius: 14px; padding: 16px; backdrop-filter: blur(10px); }
            
            /* LLM MATRIX */
            .llm-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 10px; }
            .llm-box { background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 8px; font-size: 11px; }
            .llm-box strong { display: block; color: #fff; font-size: 11px; margin-bottom: 2px; }
            .llm-box span { font-size: 10px; color: var(--accent-cyan); font-family: monospace; }

            /* NEXUS PREVIEW CANVAS */
            #nexus-preview-canvas { width: 100%; height: 140px; background: rgba(0,0,0,0.3); border-radius: 8px; border: 1px solid var(--panel-border); margin-top: 8px; }

            /* BOTTOM VOICE & COMMAND BAR */
            .bottom-command-bar { height: 60px; border-top: 1px solid var(--panel-border); padding: 0 24px; display: flex; align-items: center; gap: 16px; background: rgba(3, 7, 18, 0.98); }
            .cmd-input-container { flex: 1; display: flex; align-items: center; background: rgba(15, 25, 45, 0.8); border: 1px solid var(--panel-border); border-radius: 30px; padding: 4px 6px 4px 20px; box-shadow: 0 0 15px rgba(0,240,255,0.05); }
            .cmd-input-container:focus-within { border-color: var(--accent-cyan); box-shadow: 0 0 20px rgba(0,240,255,0.2); }
            .cmd-input { flex: 1; background: transparent; border: none; outline: none; color: #fff; font-size: 13px; }
            .cmd-btn { padding: 10px 24px; background: var(--accent-cyan); color: #000; border: none; border-radius: 24px; font-weight: 800; font-size: 12px; cursor: pointer; letter-spacing: 1px; }
        </style>
    </head>
    <body>
        <!-- TOP HUD -->
        <header>
            <div class="header-brand">
                <div class="logo-icon">P</div>
                <div class="header-title">PETER COMMAND CENTER</div>
            </div>
            
            <div class="sys-status">
                <div class="status-dot"></div>
                SYSTEM STATUS: OPTIMAL
            </div>

            <div id="live-clock" class="clock-display">00:00:00</div>
        </header>

        <!-- MAIN LAYOUT -->
        <div class="command-grid">
            <!-- LEFT NAVIGATION & VOICE -->
            <aside class="sidebar-panel">
                <div class="nav-menu">
                    <div class="nav-item active">🌐 Command Center</div>
                    <div class="nav-item">🧠 AI Core & Memory</div>
                    <div class="nav-item">🕸️ Nexus 3D Graph</div>
                    <div class="nav-item">📲 Telegram Bot</div>
                    <div class="nav-item">⚙️ System Settings</div>
                </div>

                <div class="voice-widget">
                    <div style="font-size: 11px; font-weight: 700; color: var(--accent-cyan); letter-spacing: 1px;">VOICE ENGINE</div>
                    <div class="mic-btn" onclick="alert('Modalità Open-Mic in ascolto continuativo...')">🎙️</div>
                    <div style="font-size: 10px; color: var(--text-dim);">Tap to Start Voice Chat</div>
                </div>
            </aside>

            <!-- CENTER WORKSPACE -->
            <main class="center-workspace">
                <!-- 3D NEURAL SPHERE -->
                <div class="core-visualizer">
                    <canvas id="core-canvas"></canvas>
                    <div class="core-overlay-text">
                        <h2>PETER AI CORE</h2>
                        <p>v3.0.0 // GROQ MULTI-MODEL AGENT</p>
                    </div>
                </div>

                <!-- LIVE FEED / CHAT -->
                <section class="feed-panel">
                    <div class="panel-header">
                        <span>LIVE INTELLIGENCE CHAT FEED</span>
                        <span style="font-size: 10px; color: var(--accent-green);">● INTERACTION READY</span>
                    </div>
                    <div id="chat-feed">
                        <div class="msg peter">Sistemi di bordo operativi, Marco. Groq Multi-Model Agent pronto. Invia un comando o richiedi media.</div>
                    </div>
                </section>
            </main>

            <!-- RIGHT MONITORS -->
            <aside class="right-sidebar">
                <!-- LLMs MONITOR -->
                <div class="widget-card">
                    <div class="panel-header" style="padding: 0 0 10px 0; border: none;">LLM ARCHITECTURE STATUS</div>
                    <div class="llm-grid">
                        <div class="llm-box">
                            <strong>Router (Model 1)</strong>
                            <span>gpt-oss-20b</span>
                        </div>
                        <div class="llm-box">
                            <strong>Core (Model 2)</strong>
                            <span>gpt-oss-120b</span>
                        </div>
                        <div class="llm-box">
                            <strong>Facts (Model 3)</strong>
                            <span>qwen3.8-27b</span>
                        </div>
                        <div class="llm-box">
                            <strong>Database</strong>
                            <span>Supabase DB</span>
                        </div>
                    </div>
                </div>

                <!-- MEMORY INSIGHTS & NEXUS PREVIEW -->
                <div class="widget-card">
                    <div class="panel-header" style="padding: 0 0 10px 0; border: none;">
                        <span>NEXUS GRAPH & MEMORY</span>
                        <span id="fact-count-badge" style="font-size: 10px; color: var(--accent-cyan);">0 Facts</span>
                    </div>
                    <div id="memory-facts-preview" style="font-size: 11px; color: var(--text-dim); max-height: 80px; overflow-y: auto;">
                        Sincronizzazione archivio Supabase...
                    </div>
                    <canvas id="nexus-preview-canvas"></canvas>
                </div>
            </aside>
        </div>

        <!-- BOTTOM VOICE & COMMAND BAR -->
        <footer class="bottom-command-bar">
            <div class="cmd-input-container">
                <input type="text" id="cmd-input" class="cmd-input" placeholder="TALK TO PETER — Scrivi un comando, cerca sul web o richiedi musica/video..." autocomplete="off" />
                <button type="button" id="send-cmd-btn" class="cmd-btn">EXECUTE</button>
            </div>
        </footer>

        <script>
            // Live Clock
            setInterval(() => {
                const now = new Date();
                document.getElementById('live-clock').innerText = now.toTimeString().split(' ')[0];
            }, 1000);

            // 3D Wireframe Neural Core Animation
            (function initCore3D() {
                const canvas = document.getElementById('core-canvas');
                const ctx = canvas.getContext('2d');
                let width = canvas.width = canvas.parentElement.clientWidth;
                let height = canvas.height = canvas.parentElement.clientHeight;

                let points = [];
                const numPoints = 60;
                const radius = 80;

                for (let i = 0; i < numPoints; i++) {
                    let theta = Math.acos(2 * Math.random() - 1);
                    let phi = 2 * Math.PI * Math.random();
                    points.push({
                        x: radius * Math.sin(theta) * Math.cos(phi),
                        y: radius * Math.sin(theta) * Math.sin(phi),
                        z: radius * Math.cos(theta)
                    });
                }

                let angleX = 0.005;
                let angleY = 0.008;

                function animate() {
                    ctx.clearRect(0, 0, width, height);
                    let cx = width / 2;
                    let cy = height / 2;

                    points.forEach(p => {
                        let x1 = p.x * Math.cos(angleY) - p.z * Math.sin(angleY);
                        let z1 = p.x * Math.sin(angleY) + p.z * Math.cos(angleY);

                        let y2 = p.y * Math.cos(angleX) - z1 * Math.sin(angleX);
                        let z2 = p.y * Math.sin(angleX) + z1 * Math.cos(angleX);

                        p.x = x1; p.y = y2; p.z = z2;

                        let scale = 250 / (250 + p.z);
                        let px = cx + p.x * scale;
                        let py = cy + p.y * scale;

                        ctx.beginPath();
                        ctx.arc(px, py, 2 * scale, 0, Math.PI * 2);
                        ctx.fillStyle = '#00f0ff';
                        ctx.fill();
                    });

                    requestAnimationFrame(animate);
                }
                animate();
            })();

            // Chat Feed Logic
            const input = document.getElementById('cmd-input');
            const btn = document.getElementById('send-cmd-btn');
            const feed = document.getElementById('chat-feed');

            async function sendMessage() {
                const text = input.value.trim();
                if(!text) return;

                appendMsg(text, 'user');
                input.value = '';

                try {
                    const res = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: text })
                    });
                    const data = await res.json();
                    if(data.reply) {
                        appendMsg(data.reply, 'peter', data.query_used, data.media);
                        loadBrainSummary();
                    }
                } catch(e) {
                    appendMsg("Errore di comunicazione col server.", "peter");
                }
            }

            btn.onclick = sendMessage;
            input.onkeypress = (e) => { if(e.key === 'Enter') sendMessage(); };

            function appendMsg(text, sender, toolUsed=null, media=null) {
                const div = document.createElement('div');
                div.className = `msg ${sender}`;
                let html = '';
                if(toolUsed) html += `<div class="tool-badge">⚡ ${toolUsed}</div><br>`;
                html += text;
                if(media && media.embed_url) {
                    html += `<div class="media-box"><iframe src="${media.embed_url}" allow="autoplay; encrypted-media" allowfullscreen></iframe></div>`;
                }
                div.innerHTML = html;
                feed.appendChild(div);
                feed.scrollTop = feed.scrollHeight;
            }

            // Sync Facts & Nexus
            async function loadBrainSummary() {
                try {
                    const res = await fetch('/memories');
                    const data = await res.json();
                    if(data.connected && data.long_term_facts) {
                        document.getElementById('fact-count-badge').innerText = `${data.long_term_facts.length} Facts`;
                        document.getElementById('memory-facts-preview').innerHTML = data.long_term_facts.slice(0, 3).map(f => `<div>🧠 ${f.fact}</div>`).join('');
                    }
                } catch(e){}
            }
            loadBrainSummary();
        </script>
    </body>
    </html>
    """
