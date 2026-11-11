def get_dashboard_html() -> str:
    return """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PETER HUD OS v7.0</title>
        <style>
            :root {
                --bg-main: #060913;
                --panel-bg: rgba(13, 22, 41, 0.65);
                --glass-border: rgba(0, 240, 255, 0.18);
                --accent-cyan: #00f0ff;
                --accent-purple: #8b5cf6;
                --accent-green: #10b981;
                --text-bright: #f8fafc;
                --text-dim: #94a3b8;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            body { background: radial-gradient(circle at 50% 20%, #0f172a 0%, #060913 100%); color: var(--text-bright); height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
            
            header { height: 56px; border-bottom: 1px solid var(--glass-border); padding: 0 24px; display: flex; align-items: center; justify-content: space-between; background: rgba(6, 9, 19, 0.8); backdrop-filter: blur(20px); z-index: 100; }
            .header-brand { display: flex; align-items: center; gap: 12px; }
            .logo-orb { width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple)); display: flex; align-items: center; justify-content: center; box-shadow: 0 0 15px rgba(0, 240, 255, 0.4); font-weight: 900; font-size: 13px; color: #000; }
            .header-title { font-size: 13px; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; background: linear-gradient(90deg, #fff, var(--accent-cyan)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            
            .sys-badge { display: flex; align-items: center; gap: 8px; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); padding: 4px 14px; border-radius: 30px; font-size: 11px; color: var(--accent-green); font-weight: 600; letter-spacing: 1px; }
            .clock-display { font-family: monospace; font-size: 14px; color: var(--accent-cyan); letter-spacing: 2px; }

            .command-grid { flex: 1; display: grid; grid-template-columns: 260px 1fr 340px; gap: 16px; padding: 16px; height: calc(100vh - 116px); overflow: hidden; }

            .sidebar-panel { background: var(--panel-bg); border: 1px solid var(--glass-border); border-radius: 20px; padding: 18px; display: flex; flex-direction: column; gap: 16px; backdrop-filter: blur(24px); box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
            .nav-menu { display: flex; flex-direction: column; gap: 8px; }
            .nav-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 12px; font-size: 12px; font-weight: 600; color: var(--text-dim); cursor: pointer; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); }
            .nav-item.active, .nav-item:hover { background: linear-gradient(90deg, rgba(0, 240, 255, 0.12), transparent); color: var(--accent-cyan); border-left: 3px solid var(--accent-cyan); transform: translateX(2px); }

            /* MINI AVATAR VISUALE DI PETER */
            .peter-avatar-card { background: rgba(0,0,0,0.4); border: 1px solid var(--glass-border); border-radius: 16px; padding: 14px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 8px; position: relative; overflow: hidden; }
            #peter-avatar-canvas { width: 140px; height: 140px; border-radius: 50%; cursor: pointer; }
            .avatar-status-tag { font-size: 9px; font-family: monospace; letter-spacing: 1.5px; color: var(--accent-cyan); background: rgba(0,240,255,0.1); padding: 3px 10px; border-radius: 12px; border: 1px solid rgba(0,240,255,0.3); }

            .center-workspace { display: grid; grid-template-rows: 290px 1fr; gap: 16px; height: 100%; overflow: hidden; }
            .view-tab { display: none; height: 100%; width: 100%; }
            .view-tab.active { display: flex; }

            .hud-screen { background: var(--panel-bg); border: 1px solid var(--glass-border); border-radius: 20px; position: relative; overflow: hidden; display: flex; flex-direction: column; width: 100%; backdrop-filter: blur(20px); }
            .hud-screen-header { padding: 10px 20px; background: rgba(0,0,0,0.3); border-bottom: 1px solid var(--glass-border); font-size: 10px; font-family: monospace; color: var(--accent-cyan); display: flex; justify-content: space-between; }
            #hud-screen-content { flex: 1; padding: 14px; overflow: hidden; display: flex; align-items: center; justify-content: center; position: relative; }

            .feed-panel { background: var(--panel-bg); border: 1px solid var(--glass-border); border-radius: 20px; display: flex; flex-direction: column; overflow: hidden; width: 100%; backdrop-filter: blur(20px); }
            .panel-header { padding: 12px 20px; border-bottom: 1px solid var(--glass-border); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--accent-cyan); display: flex; justify-content: space-between; align-items: center; }
            
            #chat-feed { flex: 1; overflow-y: auto; padding: 18px; display: flex; flex-direction: column; gap: 12px; scroll-behavior: smooth; }
            .msg { max-width: 78%; padding: 12px 16px; border-radius: 16px; font-size: 13px; line-height: 1.5; word-wrap: break-word; }
            .msg.user { align-self: flex-end; background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue)); color: #fff; border-bottom-right-radius: 4px; box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3); }
            .msg.peter { align-self: flex-start; background: rgba(15, 23, 42, 0.85); border: 1px solid var(--glass-border); border-bottom-left-radius: 4px; }
            
            .right-sidebar { display: flex; flex-direction: column; gap: 16px; height: 100%; overflow-y: auto; }
            .widget-card { background: var(--panel-bg); border: 1px solid var(--glass-border); border-radius: 20px; padding: 16px; backdrop-filter: blur(20px); box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
            
            .fact-item { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 11px; }
            .fact-actions { display: flex; gap: 6px; }
            .fact-btn { background: transparent; border: none; color: var(--text-dim); cursor: pointer; font-size: 12px; transition: color 0.2s; }
            .fact-btn:hover { color: var(--accent-cyan); }

            .reasoning-box { background: rgba(0,0,0,0.4); border: 1px solid rgba(0,240,255,0.15); border-radius: 10px; padding: 10px; font-size: 10px; font-family: monospace; color: var(--accent-cyan); max-height: 100px; overflow-y: auto; }

            .bottom-command-bar { height: 64px; border-top: 1px solid var(--glass-border); padding: 0 24px; display: flex; align-items: center; gap: 16px; background: rgba(6, 9, 19, 0.95); backdrop-filter: blur(20px); }
            .cmd-input-container { flex: 1; display: flex; align-items: center; background: rgba(15, 23, 42, 0.6); border: 1px solid var(--glass-border); border-radius: 30px; padding: 6px 8px 6px 20px; transition: border-color 0.3s; }
            .cmd-input-container:focus-within { border-color: var(--accent-cyan); box-shadow: 0 0 15px rgba(0,240,255,0.15); }
            .cmd-input { flex: 1; background: transparent; border: none; outline: none; color: #fff; font-size: 13px; }
            .cmd-btn { padding: 10px 24px; background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)); color: #000; border: none; border-radius: 24px; font-weight: 800; font-size: 12px; cursor: pointer; transition: transform 0.2s; }
            .cmd-btn:hover { transform: scale(1.03); }

            #nexus-graph-canvas { width: 100%; height: 100%; display: block; background: #060913; cursor: grab; }

            .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 200; align-items: center; justify-content: center; }
            .modal-box { background: var(--panel-bg); border: 1px solid var(--accent-cyan); border-radius: 20px; padding: 24px; width: 90%; max-width: 500px; }
            .input-box { background: rgba(0,0,0,0.5); border: 1px solid var(--glass-border); border-radius: 8px; padding: 10px; color: #fff; font-size: 12px; width: 100%; outline: none; margin-bottom: 12px; }
            .action-btn { background: var(--accent-cyan); color: #000; border: none; padding: 10px 20px; border-radius: 8px; font-size: 11px; font-weight: 700; cursor: pointer; }
        </style>
    </head>
    <body>
        <header>
            <div class="header-brand">
                <div class="logo-orb">P</div>
                <div class="header-title">PETER HUD COMMAND CENTER</div>
            </div>
            
            <div class="sys-badge">
                <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--accent-green); box-shadow: 0 0 8px var(--accent-green);"></span>
                PETER AGENT: ONLINE
            </div>

            <div id="live-clock" class="clock-display">00:00:00</div>
        </header>

        <div class="command-grid">
            <aside class="sidebar-panel">
                <div class="nav-menu">
                    <div class="nav-item active" onclick="switchMainView('hud')">🌐 Dashboard AI</div>
                    <div class="nav-item" onclick="switchMainView('nexus')">🕸️ Nexus 3D Graph</div>
                    <div class="nav-item" onclick="openSettingsModal()">⚙️ Impostazioni</div>
                </div>

                <!-- MINI AVATAR PROCEDURALE REATTIVO -->
                <div class="peter-avatar-card">
                    <canvas id="peter-avatar-canvas" title="Clicca per parlare a voce con Peter"></canvas>
                    <div id="avatar-status-badge" class="avatar-status-tag">STATUS // IDLE</div>
                    <div style="font-size: 10px; color: var(--text-dim);">Clicca l'avatar per la modalità Voce</div>
                </div>
            </aside>

            <main class="center-workspace">
                <div id="view-hud" class="view-tab active" style="flex-direction: column; gap: 16px;">
                    <div class="hud-screen">
                        <div class="hud-screen-header">
                            <span>REACTIVE VISUAL HUD</span>
                            <span id="hud-status-badge">STANDBY // INTERACTIVE CORE</span>
                        </div>
                        <div id="hud-screen-content">
                            <div id="hud-default-overlay" style="text-align: center; z-index: 2;">
                                <h2 style="font-size: 24px; font-weight: 900; letter-spacing: 4px; background: linear-gradient(90deg, #fff, var(--accent-cyan)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">PETER COMPANION CORE</h2>
                                <p style="font-size: 11px; font-family: monospace; color: var(--accent-cyan); letter-spacing: 2px; margin-top: 4px;">VISUAL MONITOR & EMBED READY</p>
                            </div>
                        </div>
                    </div>

                    <section class="feed-panel">
                        <div class="panel-header">
                            <span>LIVE DIALOG FEED</span>
                            <span style="font-size: 10px; color: var(--accent-green);">● VOICE & CHAT ENABLED</span>
                        </div>
                        <div id="chat-feed">
                            <div class="msg peter">Ciao Marco! Ho aggiornato il mio avatar visivo e attivato la sintesi vocale ad alta definizione. Ora posso parlare, ascoltare e mandare messaggi su Telegram!</div>
                        </div>
                    </section>
                </div>

                <div id="view-nexus" class="view-tab" style="position: relative; overflow: hidden; border-radius: 20px; border: 1px solid var(--glass-border);">
                    <canvas id="nexus-graph-canvas"></canvas>
                    <div style="position: absolute; top: 16px; left: 16px; background: rgba(6,9,19,0.85); padding: 10px 16px; border-radius: 12px; border: 1px solid var(--accent-cyan); font-size: 11px;">
                        <strong style="color:var(--accent-cyan);">NEXUS 3D GALAXIES</strong><br>
                        <span style="color:var(--text-dim);">Trascina per ruotare // Clicca nodi per dettagli</span>
                    </div>
                </div>
            </main>

            <aside class="right-sidebar">
                <div class="widget-card" style="flex: 1; display: flex; flex-direction: column;">
                    <div class="panel-header" style="padding: 0 0 10px 0; border: none;">MEMORIA A LUNGO TERMINE (EDITABLE)</div>
                    <div id="facts-preview" style="flex: 1; overflow-y: auto;">Caricamento memorie...</div>
                </div>

                <div class="widget-card">
                    <div class="panel-header" style="padding: 0 0 6px 0; border: none;">REASONING STREAM</div>
                    <div id="reasoning-preview" class="reasoning-box">> Groq Multi-Model Engine in attesa...</div>
                </div>
            </aside>
        </div>

        <footer class="bottom-command-bar">
            <div class="cmd-input-container">
                <input type="text" id="cmd-input" class="cmd-input" placeholder="Parla con Peter, chiedi un video o manda una nota vocale su Telegram..." autocomplete="off" />
                <button type="button" id="send-cmd-btn" class="cmd-btn">INVIA</button>
            </div>
        </footer>

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
            let currentAvatarState = 'IDLE'; // IDLE, THINKING, SPEAKING, LISTENING

            setInterval(() => {
                const now = new Date();
                document.getElementById('live-clock').innerText = now.toTimeString().split(' ')[0];
            }, 1000);

            function switchMainView(view) {
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                document.querySelectorAll('.view-tab').forEach(v => v.classList.remove('active'));
                event.target.classList.add('active');
                
                if(view === 'hud') {
                    document.getElementById('view-hud').classList.add('active');
                } else if(view === 'nexus') {
                    document.getElementById('view-nexus').classList.add('active');
                    loadNexus3D();
                }
            }

            // MOTORE VISUALE AVATAR PROCEDURALE 3D DI PETER
            (function initPeterAvatar() {
                const canvas = document.getElementById('peter-avatar-canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = 140; canvas.height = 140;
                let angle = 0;

                function renderAvatar() {
                    ctx.clearRect(0, 0, 140, 140);
                    const cx = 70, cy = 70;
                    angle += (currentAvatarState === 'THINKING' ? 0.08 : 0.02);

                    // Aura pulsante esterna
                    let auraColor = '#00f0ff';
                    if(currentAvatarState === 'SPEAKING') auraColor = '#8b5cf6';
                    if(currentAvatarState === 'LISTENING') auraColor = '#ec4899';
                    if(currentAvatarState === 'THINKING') auraColor = '#f59e0b';

                    document.getElementById('avatar-status-badge').innerText = `STATUS // ${currentAvatarState}`;
                    document.getElementById('avatar-status-badge').style.borderColor = auraColor;

                    let radiusPulse = 42 + Math.sin(angle * 3) * (currentAvatarState === 'SPEAKING' ? 8 : 3);
                    ctx.beginPath();
                    ctx.arc(cx, cy, radiusPulse, 0, Math.PI * 2);
                    ctx.strokeStyle = auraColor;
                    ctx.lineWidth = 2;
                    ctx.stroke();

                    // Anelli Orbitali Interattivi
                    for(let i = 0; i < 3; i++) {
                        ctx.save();
                        ctx.translate(cx, cy);
                        ctx.rotate(angle * (i % 2 === 0 ? 1 : -1) + (i * Math.PI / 3));
                        ctx.beginPath();
                        ctx.ellipse(0, 0, 32 + i * 6, 12, 0, 0, Math.PI * 2);
                        ctx.strokeStyle = auraColor;
                        ctx.globalAlpha = 0.45;
                        ctx.stroke();
                        ctx.restore();
                    }

                    // Nucleo Neurale
                    ctx.beginPath();
                    ctx.arc(cx, cy, 14 + Math.cos(angle * 2) * 2, 0, Math.PI * 2);
                    ctx.fillStyle = auraColor;
                    ctx.shadowBlur = 20;
                    ctx.shadowColor = auraColor;
                    ctx.fill();
                    ctx.shadowBlur = 0;

                    requestAnimationFrame(renderAvatar);
                }
                renderAvatar();

                canvas.onclick = toggleVoiceSession;
            })();

            // NATIVE TTS SPEECH IN BROWSER
            async function playPeterSpeech(text) {
                currentAvatarState = 'SPEAKING';
                try {
                    const res = await fetch('/api/tts', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ text: text })
                    });
                    if(res.ok) {
                        const blob = await res.blob();
                        const audio = new Audio(URL.createObjectURL(blob));
                        audio.onended = () => { currentAvatarState = 'IDLE'; };
                        audio.play();
                    } else {
                        currentAvatarState = 'IDLE';
                    }
                } catch(e) { currentAvatarState = 'IDLE'; }
            }

            function updateHudScreen(screen) {
                const container = document.getElementById('hud-screen-content');
                const badge = document.getElementById('hud-status-badge');
                if(!screen || screen.type === 'NONE') return;

                badge.innerText = `ACTIVE DISPLAY // ${screen.type}`;

                if(screen.type === 'MEDIA_PLAYER' && screen.embed_url) {
                    container.innerHTML = `
                        <div style="width:100%; height:100%; display:flex; flex-direction:column; gap:8px; justify-content:center; align-items:center;">
                            <iframe src="${screen.embed_url}" style="width:100%; max-width:540px; height:210px; border:none; border-radius:14px; border:1px solid var(--accent-cyan);" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                            ${screen.watch_url ? `<a href="${screen.watch_url}" target="_blank" style="color:var(--accent-cyan); font-size:11px; text-decoration:none;">🔗 Apri in scheda YouTube</a>` : ''}
                        </div>
                    `;
                } else if(screen.type === 'PERSON_CARD' && screen.person) {
                    container.innerHTML = `
                        <div style="background:rgba(15,23,42,0.95); border:1px solid var(--accent-cyan); padding:20px; border-radius:16px; text-align:center; max-width:320px; z-index:5;">
                            <div style="font-size:36px; margin-bottom:4px;">👤</div>
                            <h3 style="color:var(--accent-cyan); font-size:18px;">${screen.person.name}</h3>
                            <p style="font-size:11px; color:var(--text-dim); margin-bottom:8px;">Livello: ${screen.person.category || 'Amicizia'}</p>
                            <p style="font-size:12px; line-height:1.4;">${screen.person.notes || 'Registrato nel Grafo Nexus'}</p>
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
                currentAvatarState = 'THINKING';

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
                        if(data.reasoning) document.getElementById('reasoning-preview').innerText = `> ${data.reasoning}`;
                        playPeterSpeech(data.reply);
                        loadBrainSummary();
                    }
                } catch(e) {
                    appendMsg("Errore di connessione.", "peter");
                    currentAvatarState = 'IDLE';
                }
            }
            btn.onclick = sendMessage;
            input.onkeypress = (e) => { if(e.key === 'Enter') sendMessage(); };

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
                        document.getElementById('facts-preview').innerHTML = data.long_term_facts.map(f => `
                            <div class="fact-item">
                                <span id="fact-text-${f.id}">🧠 ${f.fact}</span>
                                <div class="fact-actions">
                                    <button class="fact-btn" onclick="editFact('${f.id}', '${f.fact.replace(/'/g, "\\'")}')">✏️</button>
                                    <button class="fact-btn" onclick="deleteFact('${f.id}')">🗑️</button>
                                </div>
                            </div>
                        `).join('');
                    }
                } catch(e){}
            }

            async function editFact(id, oldText) {
                const newText = prompt("Modifica fatto permanente:", oldText);
                if(newText && newText !== oldText) {
                    await fetch(`/api/facts/${id}`, {
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ fact: newText })
                    });
                    loadBrainSummary();
                }
            }

            async function deleteFact(id) {
                if(confirm("Eliminare questo fatto?")) {
                    await fetch(`/api/facts/${id}`, { method: 'DELETE' });
                    loadBrainSummary();
                }
            }

            // SESSIONE VOCALE WEBSOCKET
            let ws = null;
            let mediaRecorder = null;
            let isRecording = false;

            function toggleVoiceSession() {
                if(!isRecording) {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    ws = new WebSocket(`${protocol}//${window.location.host}/ws/voice`);
                    
                    ws.onopen = () => {
                        navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
                            mediaRecorder = new MediaRecorder(stream);
                            mediaRecorder.ondataavailable = e => { if(ws.readyState === WebSocket.OPEN) ws.send(e.data); };
                            mediaRecorder.start(2000);
                            isRecording = true;
                            currentAvatarState = 'LISTENING';
                        });
                    };

                    ws.onmessage = async (event) => {
                        if(typeof event.data === 'string') {
                            const data = JSON.parse(event.data);
                            appendMsg(data.user_text, 'user');
                            appendMsg(data.reply_text, 'peter');
                            if(data.screen) updateHudScreen(data.screen);
                            if(data.reasoning) document.getElementById('reasoning-preview').innerText = `> ${data.reasoning}`;
                        } else {
                            currentAvatarState = 'SPEAKING';
                            const blob = new Blob([event.data], { type: 'audio/mp3' });
                            const audio = new Audio(URL.createObjectURL(blob));
                            audio.onended = () => { currentAvatarState = 'LISTENING'; };
                            audio.play();
                        }
                    };
                } else {
                    if(mediaRecorder) mediaRecorder.stop();
                    if(ws) ws.close();
                    isRecording = false;
                    currentAvatarState = 'IDLE';
                }
            }

            function openSettingsModal() { document.getElementById('settings-modal').style.display = 'flex'; }
            function closeSettingsModal() { document.getElementById('settings-modal').style.display = 'none'; }

            loadBrainSummary();
        </script>
    </body>
    </html>
    """
