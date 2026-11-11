def get_dashboard_html() -> str:
    return """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PETER COMMAND CENTER v4.0</title>
        <style>
            :root {
                --bg-main: #030712;
                --panel-bg: rgba(10, 20, 38, 0.85);
                --panel-border: rgba(0, 240, 255, 0.2);
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

            .command-grid { flex: 1; display: grid; grid-template-columns: 240px 1fr 340px; gap: 14px; padding: 14px; height: calc(100vh - 114px); overflow: hidden; }

            .sidebar-panel { background: var(--panel-bg); border: 1px solid var(--panel-border); border-radius: 14px; padding: 16px; display: flex; flex-direction: column; gap: 16px; backdrop-filter: blur(10px); }
            .nav-menu { display: flex; flex-direction: column; gap: 6px; }
            .nav-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; color: var(--text-dim); text-decoration: none; cursor: pointer; transition: all 0.2s; }
            .nav-item.active, .nav-item:hover { background: rgba(0, 240, 255, 0.08); color: var(--accent-cyan); border-left: 3px solid var(--accent-cyan); }
            
            .voice-widget { margin-top: auto; background: rgba(0, 240, 255, 0.03); border: 1px solid var(--panel-border); border-radius: 12px; padding: 16px; text-align: center; }
            .mic-btn { width: 56px; height: 56px; border-radius: 50%; border: 2px solid var(--accent-cyan); background: rgba(0,240,255,0.1); color: var(--accent-cyan); font-size: 20px; display: flex; align-items: center; justify-content: center; margin: 10px auto; cursor: pointer; box-shadow: 0 0 20px rgba(0,240,255,0.2); transition: all 0.3s; }
            .mic-btn.recording { background: #ef4444; border-color: #f87171; box-shadow: 0 0 30px #ef4444; }

            .center-workspace { display: grid; grid-template-rows: 320px 1fr; gap: 14px; height: 100%; overflow: hidden; }
            
            /* SCHERMO REATTIVO HUD */
            .hud-screen { background: var(--panel-bg); border: 1px solid var(--panel-border); border-radius: 14px; position: relative; overflow: hidden; display: flex; flex-direction: column; }
            .hud-screen-header { padding: 8px 16px; background: rgba(0,0,0,0.4); border-bottom: 1px solid var(--panel-border); font-size: 10px; font-family: monospace; color: var(--accent-cyan); display: flex; justify-content: space-between; }
            #hud-screen-content { flex: 1; padding: 14px; overflow-y: auto; display: flex; align-items: center; justify-content: center; position: relative; }
            #core-canvas { width: 100%; height: 100%; position: absolute; top:0; left:0; pointer-events: none; opacity: 0.3; }

            .feed-panel { background: var(--panel-bg); border: 1px solid var(--panel-border); border-radius: 14px; display: flex; flex-direction: column; overflow: hidden; }
            .panel-header { padding: 12px 16px; border-bottom: 1px solid var(--panel-border); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--accent-cyan); display: flex; justify-content: space-between; align-items: center; }
            
            #chat-feed { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; scroll-behavior: smooth; }
            .msg { max-width: 80%; padding: 10px 14px; border-radius: 12px; font-size: 13px; line-height: 1.5; word-wrap: break-word; }
            .msg.user { align-self: flex-end; background: linear-gradient(135deg, #1d4ed8, #2563eb); color: #fff; border-bottom-right-radius: 2px; }
            .msg.peter { align-self: flex-start; background: rgba(15, 25, 45, 0.9); border: 1px solid var(--panel-border); border-bottom-left-radius: 2px; }
            
            .right-sidebar { display: flex; flex-direction: column; gap: 14px; height: 100%; overflow-y: auto; }
            .widget-card { background: var(--panel-bg); border: 1px solid var(--panel-border); border-radius: 14px; padding: 16px; backdrop-filter: blur(10px); }
            
            .bottom-command-bar { height: 60px; border-top: 1px solid var(--panel-border); padding: 0 24px; display: flex; align-items: center; gap: 16px; background: rgba(3, 7, 18, 0.98); }
            .cmd-input-container { flex: 1; display: flex; align-items: center; background: rgba(15, 25, 45, 0.8); border: 1px solid var(--panel-border); border-radius: 30px; padding: 4px 6px 4px 16px; }
            .cmd-input { flex: 1; background: transparent; border: none; outline: none; color: #fff; font-size: 13px; }
            .cmd-btn { padding: 10px 24px; background: var(--accent-cyan); color: #000; border: none; border-radius: 24px; font-weight: 800; font-size: 12px; cursor: pointer; }
            .upload-btn { background: transparent; border: none; color: var(--accent-cyan); font-size: 18px; cursor: pointer; margin-right: 10px; }

            /* MODALE IMPOSTAZIONI */
            .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 200; align-items: center; justify-content: center; }
            .modal-box { background: var(--panel-bg); border: 1px solid var(--accent-cyan); border-radius: 14px; padding: 24px; width: 90%; max-width: 500px; }
            .input-box { background: rgba(0,0,0,0.4); border: 1px solid var(--panel-border); border-radius: 6px; padding: 8px; color: #fff; font-size: 12px; width: 100%; outline: none; margin-bottom: 10px; }
            .action-btn { background: var(--accent-cyan); color: #000; border: none; padding: 8px 16px; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer; }
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
                    <div class="nav-item active">🌐 Command Center</div>
                    <div class="nav-item" onclick="openSettingsModal()">⚙️ Impostazioni & Core</div>
                </div>

                <div class="voice-widget">
                    <div style="font-size: 11px; font-weight: 700; color: var(--accent-cyan); letter-spacing: 1px;">VOICE ENGINE</div>
                    <div id="mic-btn" class="mic-btn" onclick="toggleVoiceSession()">🎙️</div>
                    <div id="voice-status-text" style="font-size: 10px; color: var(--text-dim);">Tap to Start Voice Chat</div>
                </div>
            </aside>

            <main class="center-workspace">
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
                        <div class="msg peter">Sistemi di bordo operativi. Schermo Reattivo HUD visivo integrato. Carica immagini o invia un comando.</div>
                    </div>
                </section>
            </main>

            <aside class="right-sidebar">
                <div class="widget-card">
                    <div class="panel-header" style="padding: 0 0 10px 0; border: none;">MEMORIA A LUNGO TERMINE</div>
                    <div id="facts-preview" style="font-size: 11px; color: var(--text-dim); max-height: 200px; overflow-y: auto;">Caricamento memorie...</div>
                </div>
            </aside>
        </div>

        <footer class="bottom-command-bar">
            <div class="cmd-input-container">
                <button type="button" class="upload-btn" onclick="document.getElementById('image-upload-input').click()">📷</button>
                <input type="file" id="image-upload-input" accept="image/*" style="display:none;" onchange="uploadImageChat()" />
                <input type="text" id="cmd-input" class="cmd-input" placeholder="TALK TO PETER — Scrivi un comando, chiedi un video/opera o invia un messaggio..." autocomplete="off" />
                <button type="button" id="send-cmd-btn" class="cmd-btn">EXECUTE</button>
            </div>
        </footer>

        <!-- MODALE IMPOSTAZIONI -->
        <div id="settings-modal" class="modal-overlay">
            <div class="modal-box">
                <h3 style="color:var(--accent-cyan); margin-bottom:12px;">Impostazioni & Personalità</h3>
                <label style="font-size: 10px; color: var(--text-dim);">Tono di Voce:</label>
                <input type="text" id="p-tone" class="input-box" value="Schietto, empatico, naturale, colto e ironico." />

                <label style="font-size: 10px; color: var(--text-dim);">Importa File Contatti (.vcf):</label>
                <input type="file" id="vcf-file" accept=".vcf" class="input-box" onchange="uploadVCF()" />

                <label style="font-size: 10px; color: var(--text-dim);">Link iCal (.ics):</label>
                <input type="text" id="ical-url" class="input-box" placeholder="https://..." />
                <button class="action-btn" onclick="importICal()">Sincronizza iCal</button>
                
                <button class="action-btn" style="background:#ef4444; color:#fff; float:right;" onclick="closeSettingsModal()">Chiudi</button>
            </div>
        </div>

        <script>
            setInterval(() => {
                const now = new Date();
                document.getElementById('live-clock').innerText = now.toTimeString().split(' ')[0];
            }, 1000);

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

            function updateHudScreen(screen) {
                const container = document.getElementById('hud-screen-content');
                const badge = document.getElementById('hud-status-badge');
                if(!screen || screen.type === 'NONE') return;

                badge.innerText = `ACTIVE DISPLAY // ${screen.type}`;

                if(screen.type === 'MEDIA_PLAYER' && screen.embed_url) {
                    container.innerHTML = `<iframe src="${screen.embed_url}" style="width:100%; height:100%; border:none; border-radius:8px;" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>`;
                } else if(screen.type === 'IMAGE_PREVIEW') {
                    container.innerHTML = `
                        <div style="text-align:center; max-width:90%; max-height:90%; z-index:5;">
                            ${screen.image_url ? `<img src="${screen.image_url}" style="max-width:100%; max-height:220px; border-radius:8px; border:1px solid var(--accent-cyan);" />` : ''}
                            <h4 style="color:var(--accent-cyan); margin-top:8px;">${screen.title}</h4>
                            <p style="font-size:11px; color:var(--text-bright); margin-top:4px;">${screen.content}</p>
                        </div>
                    `;
                } else if(screen.type === 'PERSON_CARD' && screen.person) {
                    container.innerHTML = `
                        <div style="background:rgba(10,20,38,0.95); border:1px solid var(--accent-cyan); padding:20px; border-radius:12px; text-align:center; max-width:320px; z-index:5;">
                            <div style="font-size:36px; margin-bottom:6px;">👤</div>
                            <h3 style="color:var(--accent-cyan); font-size:18px;">${screen.person.name}</h3>
                            <p style="font-size:11px; color:var(--text-dim); margin-bottom:8px;">Categoria: ${screen.person.category || 'Amicizia'}</p>
                            <p style="font-size:12px;">${screen.person.notes || 'Menzionato in conversazione'}</p>
                        </div>
                    `;
                }
            }

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
                        appendMsg(data.reply, 'peter');
                        if(data.screen) updateHudScreen(data.screen);
                        loadBrainSummary();
                    }
                } catch(e) {
                    appendMsg("Errore di connessione.", "peter");
                }
            }
            btn.onclick = sendMessage;
            input.onkeypress = (e) => { if(e.key === 'Enter') sendMessage(); };

            async function uploadImageChat() {
                const fileInput = document.getElementById('image-upload-input');
                if(!fileInput.files[0]) return;
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                formData.append('message', input.value.trim());

                appendMsg("[Invio immagine in corso...]", 'user');
                input.value = '';

                try {
                    const res = await fetch('/chat/image', { method: 'POST', body: formData });
                    const data = await res.json();
                    if(data.reply) {
                        appendMsg(data.reply, 'peter');
                        if(data.screen) updateHudScreen(data.screen);
                        loadBrainSummary();
                    }
                } catch(e) {
                    appendMsg("Errore invio immagine.", "peter");
                }
            }

            function appendMsg(text, sender) {
                const div = document.createElement('div');
                div.className = `msg ${sender}`;
                div.innerText = text;
                feed.appendChild(div);
                feed.scrollTop = feed.scrollHeight;
            }

            async function loadBrainSummary() {
                try {
                    const res = await fetch('/memories');
                    const data = await res.json();
                    if(data.connected && data.long_term_facts) {
                        document.getElementById('facts-preview').innerHTML = data.long_term_facts.slice(0, 6).map(f => `
                            <div style="padding:4px 0; border-bottom:1px solid rgba(255,255,255,0.05);">🧠 ${f.fact}</div>
                        `).join('');
                    }
                } catch(e){}
            }

            function openSettingsModal() { document.getElementById('settings-modal').style.display = 'flex'; }
            function closeSettingsModal() { document.getElementById('settings-modal').style.display = 'none'; }
            
            async function uploadVCF() {
                const fileInput = document.getElementById('vcf-file');
                if(!fileInput.files[0]) return;
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                const res = await fetch('/api/import/vcf', { method: 'POST', body: formData });
                const data = await res.json();
                alert(`Importati ${data.count || 0} contatti!`);
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
                alert(`Sincronizzati ${data.count || 0} eventi!`);
            }

            loadBrainSummary();
        </script>
    </body>
    </html>
    """
