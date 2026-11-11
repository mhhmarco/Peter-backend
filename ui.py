def get_dashboard_html() -> str:
    return """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PETER COMMAND CENTER v3.5</title>
        <style>
            :root {
                --bg-main: #030712;
                --panel-bg: rgba(10, 20, 38, 0.75);
                --panel-border: rgba(0, 240, 255, 0.18);
                --accent-cyan: #00f0ff;
                --accent-blue: #1d4ed8;
                --accent-green: #10b981;
                --text-bright: #f3f4f6;
                --text-dim: #6b7280;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: "SF Pro Text", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            body { background: var(--bg-main); color: var(--text-bright); height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
            
            header { height: 54px; border-bottom: 1px solid var(--panel-border); padding: 0 24px; display: flex; align-items: center; justify-content: space-between; background: rgba(3, 7, 18, 0.95); backdrop-filter: blur(12px); z-index: 100; }
            .header-brand { display: flex; align-items: center; gap: 12px; }
            .logo-icon { width: 28px; height: 28px; border-radius: 50%; border: 2px solid var(--accent-cyan); display: flex; align-items: center; justify-content: center; box-shadow: 0 0 10px var(--accent-cyan); font-size: 11px; font-weight: 800; color: var(--accent-cyan); }
            .header-title { font-size: 14px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; }
            
            .sys-status { display: flex; align-items: center; gap: 8px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); padding: 4px 12px; border-radius: 20px; font-size: 11px; color: var(--accent-green); font-weight: 600; letter-spacing: 1px; }
            .status-dot { width: 6px; height: 6px; background: var(--accent-green); border-radius: 50%; box-shadow: 0 0 8px var(--accent-green); }
            .clock-display { font-family: monospace; font-size: 15px; color: var(--accent-cyan); letter-spacing: 1px; }

            .command-grid { flex: 1; display: grid; grid-template-columns: 240px 1fr 380px; gap: 14px; padding: 14px; height: calc(100vh - 114px); overflow: hidden; }

            .sidebar-panel { background: var(--panel-bg); border: 1px solid var(--panel-border); border-radius: 14px; padding: 16px; display: flex; flex-direction: column; gap: 16px; backdrop-filter: blur(10px); }
            .nav-menu { display: flex; flex-direction: column; gap: 6px; }
            .nav-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; color: var(--text-dim); text-decoration: none; cursor: pointer; transition: all 0.2s; }
            .nav-item.active, .nav-item:hover { background: rgba(0, 240, 255, 0.08); color: var(--accent-cyan); border-left: 3px solid var(--accent-cyan); }
            
            .voice-widget { margin-top: auto; background: rgba(0, 240, 255, 0.03); border: 1px solid var(--panel-border); border-radius: 12px; padding: 16px; text-align: center; }
            .mic-btn { width: 56px; height: 56px; border-radius: 50%; border: 2px solid var(--accent-cyan); background: rgba(0,240,255,0.1); color: var(--accent-cyan); font-size: 20px; display: flex; align-items: center; justify-content: center; margin: 10px auto; cursor: pointer; box-shadow: 0 0 20px rgba(0,240,255,0.2); transition: all 0.3s; }
            .mic-btn.recording { background: #ef4444; border-color: #f87171; box-shadow: 0 0 30px #ef4444; animation: pulse 1.5s infinite; }
            @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.08); } 100% { transform: scale(1); } }

            .center-workspace { display: grid; grid-template-rows: 280px 1fr; gap: 14px; height: 100%; overflow: hidden; }
            
            /* SCHERMO REATTIVO HUD */
            .hud-screen { background: var(--panel-bg); border: 1px solid var(--panel-border); border-radius: 14px; position: relative; overflow: hidden; display: flex; flex-direction: column; }
            .hud-screen-header { padding: 8px 16px; background: rgba(0,0,0,0.4); border-bottom: 1px solid var(--panel-border); font-size: 10px; font-family: monospace; color: var(--accent-cyan); display: flex; justify-content: space-between; }
            #hud-screen-content { flex: 1; padding: 14px; overflow-y: auto; display: flex; align-items: center; justify-content: center; position: relative; }
            #core-canvas { width: 100%; height: 100%; position: absolute; top:0; left:0; pointer-events: none; opacity: 0.35; }

            .feed-panel { background: var(--panel-bg); border: 1px solid var(--panel-border); border-radius: 14px; display: flex; flex-direction: column; overflow: hidden; }
            .panel-header { padding: 12px 16px; border-bottom: 1px solid var(--panel-border); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--accent-cyan); display: flex; justify-content: space-between; align-items: center; }
            
            #chat-feed { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; scroll-behavior: smooth; }
            .msg { max-width: 80%; padding: 10px 14px; border-radius: 12px; font-size: 13px; line-height: 1.5; word-wrap: break-word; }
            .msg.user { align-self: flex-end; background: linear-gradient(135deg, #1d4ed8, #2563eb); color: #fff; border-bottom-right-radius: 2px; }
            .msg.peter { align-self: flex-start; background: rgba(15, 25, 45, 0.9); border: 1px solid var(--panel-border); border-bottom-left-radius: 2px; }
            
            .right-sidebar { display: flex; flex-direction: column; gap: 14px; height: 100%; overflow-y: auto; }
            .widget-card { background: var(--panel-bg); border: 1px solid var(--panel-border); border-radius: 14px; padding: 16px; backdrop-filter: blur(10px); }
            
            .input-box { background: rgba(0,0,0,0.3); border: 1px solid var(--panel-border); border-radius: 6px; padding: 8px; color: #fff; font-size: 11px; width: 100%; outline: none; }
            .action-btn { background: var(--accent-cyan); color: #000; border: none; padding: 6px 12px; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer; margin-top: 6px; }

            .bottom-command-bar { height: 60px; border-top: 1px solid var(--panel-border); padding: 0 24px; display: flex; align-items: center; gap: 16px; background: rgba(3, 7, 18, 0.98); }
            .cmd-input-container { flex: 1; display: flex; align-items: center; background: rgba(15, 25, 45, 0.8); border: 1px solid var(--panel-border); border-radius: 30px; padding: 4px 6px 4px 20px; }
            .cmd-input { flex: 1; background: transparent; border: none; outline: none; color: #fff; font-size: 13px; }
            .cmd-btn { padding: 10px 24px; background: var(--accent-cyan); color: #000; border: none; border-radius: 24px; font-weight: 800; font-size: 12px; cursor: pointer; }
        </style>
    </head>
    <body>
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

        <div class="command-grid">
            <aside class="sidebar-panel">
                <div class="nav-menu">
                    <div class="nav-item active" onclick="showPanel('center')">🌐 Command Center</div>
                    <div class="nav-item" onclick="showPanel('personality')">🧠 Personalità & Core</div>
                    <div class="nav-item" onclick="showPanel('imports')">📲 Contatti & iCal</div>
                </div>

                <div class="voice-widget">
                    <div style="font-size: 11px; font-weight: 700; color: var(--accent-cyan); letter-spacing: 1px;">VOICE ENGINE</div>
                    <div id="mic-btn" class="mic-btn" onclick="toggleVoiceSession()">🎙️</div>
                    <div id="voice-status-text" style="font-size: 10px; color: var(--text-dim);">Tap to Start Voice Chat</div>
                </div>
            </aside>

            <main class="center-workspace">
                <!-- SCHERMO REATTIVO VISIVO HUD -->
                <div class="hud-screen">
                    <div class="hud-screen-header">
                        <span>REACTIVE HUD DISPLAY</span>
                        <span id="hud-status-badge">STANDBY // SFERA NEURALE</span>
                    </div>
                    <div id="hud-screen-content">
                        <canvas id="core-canvas"></canvas>
                        <div id="hud-default-overlay" style="text-align: center; z-index: 2;">
                            <h2 style="font-size: 22px; font-weight: 900; letter-spacing: 4px; text-shadow: 0 0 16px var(--accent-cyan);">PETER AI CORE</h2>
                            <p style="font-size: 11px; font-family: monospace; color: var(--accent-cyan); letter-spacing: 2px;">READY // VISUAL MONITORING ACTIVE</p>
                        </div>
                    </div>
                </div>

                <section class="feed-panel">
                    <div class="panel-header">
                        <span>LIVE CHAT FEED</span>
                        <span style="font-size: 10px; color: var(--accent-green);">● INTERACTION READY</span>
                    </div>
                    <div id="chat-feed">
                        <div class="msg peter">Sistemi di bordo operativi. Lo Schermo Reattivo HUD si aggiornerà in base ai nostri argomenti.</div>
                    </div>
                </section>
            </main>

            <aside class="right-sidebar">
                <!-- PERSONALITY MATRIX PANEL -->
                <div id="personality-panel" class="widget-card">
                    <div class="panel-header" style="padding: 0 0 10px 0; border: none;">PERSONALITY MATRIX</div>
                    <label style="font-size: 10px; color: var(--text-dim);">Tono di Voce:</label>
                    <input type="text" id="p-tone" class="input-box" value="Schietto, empatico, naturale, colto e ironico." />
                    
                    <label style="font-size: 10px; color: var(--text-dim); margin-top: 8px; display:block;">Iniziativa:</label>
                    <input type="text" id="p-initiative" class="input-box" value="Alto (Suggerimenti proattivi)" />

                    <button class="action-btn" onclick="savePersonality()">Salva Personalità</button>
                </div>

                <!-- IMPORT CONTATTI & ICAL -->
                <div id="import-panel" class="widget-card">
                    <div class="panel-header" style="padding: 0 0 10px 0; border: none;">IMPORT CONTATTI & ICAL</div>
                    <label style="font-size: 10px; color: var(--text-dim);">Importa File Contatti (.vcf):</label>
                    <input type="file" id="vcf-file" accept=".vcf" class="input-box" onchange="uploadVCF()" />

                    <label style="font-size: 10px; color: var(--text-dim); margin-top: 10px; display:block;">Sincronizza Link iCal (.ics):</label>
                    <input type="text" id="ical-url" class="input-box" placeholder="https://calendar.google.com/calendar/ical/.../public/basic.ics" />
                    <button class="action-btn" onclick="importICal()">Sincronizza iCal</button>
                </div>
            </aside>
        </div>

        <footer class="bottom-command-bar">
            <div class="cmd-input-container">
                <input type="text" id="cmd-input" class="cmd-input" placeholder="TALK TO PETER — Scrivi un comando o fai una domanda..." autocomplete="off" />
                <button type="button" id="send-cmd-btn" class="cmd-btn">EXECUTE</button>
            </div>
        </footer>

        <script>
            setInterval(() => {
                const now = new Date();
                document.getElementById('live-clock').innerText = now.toTimeString().split(' ')[0];
            }, 1000);

            // 3D Core Sphere Animation
            (function initCore3D() {
                const canvas = document.getElementById('core-canvas');
                const ctx = canvas.getContext('2d');
                let width = canvas.width = canvas.parentElement.clientWidth;
                let height = canvas.height = canvas.parentElement.clientHeight;

                let points = [];
                for (let i = 0; i < 50; i++) {
                    let theta = Math.acos(2 * Math.random() - 1);
                    let phi = 2 * Math.PI * Math.random();
                    points.push({ x: 70 * Math.sin(theta) * Math.cos(phi), y: 70 * Math.sin(theta) * Math.sin(phi), z: 70 * Math.cos(theta) });
                }

                function animate() {
                    ctx.clearRect(0, 0, width, height);
                    let cx = width / 2, cy = height / 2;
                    points.forEach(p => {
                        let x1 = p.x * Math.cos(0.005) - p.z * Math.sin(0.005);
                        let z1 = p.x * Math.sin(0.005) + p.z * Math.cos(0.005);
                        p.x = x1; p.z = z1;
                        let scale = 250 / (250 + p.z);
                        ctx.beginPath(); ctx.arc(cx + p.x * scale, cy + p.y * scale, 2 * scale, 0, Math.PI * 2);
                        ctx.fillStyle = '#00f0ff'; ctx.fill();
                    });
                    requestAnimationFrame(animate);
                }
                animate();
            })();

            // AGGIORNAMENTO SCHERMO REATTIVO HUD
            function updateHudScreen(screen) {
                const container = document.getElementById('hud-screen-content');
                const badge = document.getElementById('hud-status-badge');
                if(!screen || screen.type === 'NONE') return;

                badge.innerText = `ACTIVE DISPLAY // ${screen.type}`;

                if(screen.type === 'MEDIA_PLAYER' && screen.embed_url) {
                    container.innerHTML = `<iframe src="${screen.embed_url}" style="width:100%; height:100%; border:none; border-radius:8px;" allow="autoplay"></iframe>`;
                } else if(screen.type === 'PERSON_CARD' && screen.person) {
                    container.innerHTML = `
                        <div style="background:rgba(10,20,38,0.9); border:1px solid var(--accent-cyan); padding:20px; border-radius:12px; text-align:center; max-width:320px; z-index:5;">
                            <div style="font-size:36px; margin-bottom:6px;">👤</div>
                            <h3 style="color:var(--accent-cyan); font-size:18px;">${screen.person.name}</h3>
                            <p style="font-size:11px; color:var(--text-dim); margin-bottom:8px;">Categoria: ${screen.person.category || 'Amicizia'}</p>
                            <p style="font-size:12px;">${screen.person.notes || 'Nessuna nota aggiuntiva'}</p>
                        </div>
                    `;
                } else if(screen.type === 'SEARCH_PREVIEW') {
                    container.innerHTML = `
                        <div style="background:rgba(10,20,38,0.9); border:1px solid var(--panel-border); padding:16px; border-radius:8px; max-width:440px; font-size:12px; z-index:5;">
                            <h4 style="color:var(--accent-cyan); margin-bottom:6px;">🔍 ${screen.query}</h4>
                            <p style="color:var(--text-bright);">${screen.content}</p>
                        </div>
                    `;
                }
            }

            // CHAT REST LOGIC
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
                        if(data.screen) updateHudScreen(data.screen);
                    }
                } catch(e) {
                    appendMsg("Errore di connessione.", "peter");
                }
            }
            btn.onclick = sendMessage;
            input.onkeypress = (e) => { if(e.key === 'Enter') sendMessage(); };

            function appendMsg(text, sender, toolUsed=null, media=null) {
                const div = document.createElement('div');
                div.className = `msg ${sender}`;
                let html = text;
                div.innerHTML = html;
                feed.appendChild(div);
                feed.scrollTop = feed.scrollHeight;
            }

            // FULL-DUPLEX WEBSOCKET VOICE STREAMING
            let ws = null;
            let mediaRecorder = null;
            let isRecording = false;

            function toggleVoiceSession() {
                const micBtn = document.getElementById('mic-btn');
                const statusText = document.getElementById('voice-status-text');

                if(!isRecording) {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    ws = new WebSocket(`${protocol}//${window.location.host}/ws/voice`);
                    
                    ws.onopen = () => {
                        navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
                            mediaRecorder = new MediaRecorder(stream);
                            mediaRecorder.ondataavailable = e => { if(ws.readyState === WebSocket.OPEN) ws.send(e.data); };
                            mediaRecorder.start(2500); // Invia blocchi audio ogni 2.5s
                            isRecording = true;
                            micBtn.classList.add('recording');
                            statusText.innerText = 'Ascolto in corso...';
                        });
                    };

                    ws.onmessage = async (event) => {
                        if(typeof event.data === 'string') {
                            const data = JSON.parse(event.data);
                            appendMsg(data.user_text, 'user');
                            appendMsg(data.reply_text, 'peter');
                            if(data.screen) updateHudScreen(data.screen);
                        } else {
                            // Audio risposta da Edge-TTS
                            const blob = new Blob([event.data], { type: 'audio/mp3' });
                            const audio = new Audio(URL.createObjectURL(blob));
                            audio.play();
                        }
                    };
                } else {
                    if(mediaRecorder) mediaRecorder.stop();
                    if(ws) ws.close();
                    isRecording = false;
                    micBtn.classList.remove('recording');
                    statusText.innerText = 'Tap to Start Voice Chat';
                }
            }

            // PERSONALITY & IMPORTS
            async function savePersonality() {
                const tone = document.getElementById('p-tone').value;
                const initiative = document.getElementById('p-initiative').value;
                await fetch('/api/personality', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ tone: tone, initiative_level: initiative })
                });
                alert('Personalità aggiornata!');
            }

            async function uploadVCF() {
                const fileInput = document.getElementById('vcf-file');
                if(!fileInput.files[0]) return;
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                const res = await fetch('/api/import/vcf', { method: 'POST', body: formData });
                const data = await res.json();
                alert(`Importati ${data.count || 0} contatti da file .vcf!`);
            }

            async function importICal() {
                const url = document.getElementById('ical-url').value;
                if(!url) return;
                const res = await fetch('/api/import/ical', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ url: url })
                });
                const data = await res.json();
                alert(`Sincronizzati ${data.count || 0} eventi dal link iCal!`);
            }
        </script>
    </body>
    </html>
    """
