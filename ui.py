def get_dashboard_html() -> str:
    return """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PETER HUD OS v8.1</title>
        <style>
            :root { 
                --bg-main: #060913; 
                --panel-bg: rgba(13, 22, 41, 0.75); 
                --glass-border: rgba(0, 240, 255, 0.18); 
                --accent-cyan: #00f0ff; 
                --accent-purple: #8b5cf6; 
                --accent-green: #10b981; 
                --text-bright: #f8fafc; 
                --text-dim: #94a3b8; 
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: "Inter", sans-serif; }
            body { background: radial-gradient(circle at 50% 20%, #0f172a 0%, #060913 100%); color: var(--text-bright); height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
            
            header { height: 56px; border-bottom: 1px solid var(--glass-border); padding: 0 24px; display: flex; align-items: center; justify-content: space-between; background: rgba(6, 9, 19, 0.9); backdrop-filter: blur(20px); z-index: 100; flex-shrink: 0; }
            .header-brand { display: flex; align-items: center; gap: 12px; }
            .logo-orb { width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple)); display: flex; align-items: center; justify-content: center; box-shadow: 0 0 15px rgba(0, 240, 255, 0.4); font-weight: 900; font-size: 13px; color: #000; }
            .header-title { font-size: 13px; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; background: linear-gradient(90deg, #fff, var(--accent-cyan)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            
            .sys-badge { display: flex; align-items: center; gap: 8px; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); padding: 4px 14px; border-radius: 30px; font-size: 11px; color: var(--accent-green); font-weight: 600; letter-spacing: 1px; }
            .clock-display { font-family: monospace; font-size: 14px; color: var(--accent-cyan); letter-spacing: 2px; }

            /* GRIGLIA PRINCIPALE BLOCCATA */
            .command-grid { flex: 1; display: grid; grid-template-columns: 260px 1fr 340px; gap: 16px; padding: 16px; height: calc(100vh - 120px); overflow: hidden; }

            .sidebar-panel { background: var(--panel-bg); border: 1px solid var(--glass-border); border-radius: 20px; padding: 18px; display: flex; flex-direction: column; gap: 16px; backdrop-filter: blur(24px); box-shadow: 0 8px 32px rgba(0,0,0,0.3); height: 100%; overflow: hidden; }
            .nav-menu { display: flex; flex-direction: column; gap: 8px; }
            .nav-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 12px; font-size: 12px; font-weight: 600; color: var(--text-dim); cursor: pointer; transition: all 0.25s ease; }
            .nav-item.active, .nav-item:hover { background: linear-gradient(90deg, rgba(0, 240, 255, 0.12), transparent); color: var(--accent-cyan); border-left: 3px solid var(--accent-cyan); transform: translateX(2px); }

            .peter-avatar-card { background: rgba(0,0,0,0.4); border: 1px solid var(--glass-border); border-radius: 16px; padding: 14px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 8px; flex-shrink: 0; }
            #peter-avatar-canvas { width: 130px; height: 130px; border-radius: 50%; cursor: pointer; }
            .avatar-status-tag { font-size: 9px; font-family: monospace; letter-spacing: 1.5px; color: var(--accent-cyan); background: rgba(0,240,255,0.1); padding: 3px 10px; border-radius: 12px; border: 1px solid rgba(0,240,255,0.3); }

            /* LAYOUT CENTRALE CON ALTEZZE FISSE E RIGIDE */
            .center-workspace { display: flex; flex-direction: column; gap: 16px; height: 100%; overflow: hidden; }
            .view-tab { display: none; flex-direction: column; gap: 16px; height: 100%; width: 100%; overflow: hidden; }
            .view-tab.active { display: flex; }

            /* HUD DISPLAY FISSO A 280PX */
            .hud-screen { background: var(--panel-bg); border: 1px solid var(--glass-border); border-radius: 20px; height: 280px; flex-shrink: 0; position: relative; overflow: hidden; display: flex; flex-direction: column; backdrop-filter: blur(20px); }
            .hud-screen-header { padding: 8px 16px; background: rgba(0,0,0,0.3); border-bottom: 1px solid var(--glass-border); font-size: 10px; font-family: monospace; color: var(--accent-cyan); display: flex; justify-content: space-between; flex-shrink: 0; }
            #hud-screen-content { flex: 1; padding: 12px; overflow: hidden; display: flex; align-items: center; justify-content: center; position: relative; }

            /* CHAT FEED CHE OCCUPA ESATTAMENTE LO SPAZIO RIMANENTE */
            .feed-panel { background: var(--panel-bg); border: 1px solid var(--glass-border); border-radius: 20px; flex: 1; display: flex; flex-direction: column; overflow: hidden; backdrop-filter: blur(20px); min-height: 0; }
            .panel-header { padding: 10px 16px; border-bottom: 1px solid var(--glass-border); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--accent-cyan); display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
            
            #chat-feed { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 10px; scroll-behavior: smooth; min-height: 0; }
            .msg { max-width: 80%; padding: 10px 14px; border-radius: 14px; font-size: 13px; line-height: 1.45; word-wrap: break-word; flex-shrink: 0; }
            .msg.user { align-self: flex-end; background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue)); color: #fff; border-bottom-right-radius: 4px; box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3); }
            .msg.peter { align-self: flex-start; background: rgba(15, 23, 42, 0.85); border: 1px solid var(--glass-border); border-bottom-left-radius: 4px; }
            
            .right-sidebar { display: flex; flex-direction: column; gap: 16px; height: 100%; overflow: hidden; }
            .widget-card { background: var(--panel-bg); border: 1px solid var(--glass-border); border-radius: 20px; padding: 16px; backdrop-filter: blur(20px); box-shadow: 0 8px 32px rgba(0,0,0,0.3); display: flex; flex-direction: column; overflow: hidden; }
            .widget-card.flex-grow { flex: 1; min-height: 0; }
            .widget-card.fixed-small { height: 160px; flex-shrink: 0; }
            
            #facts-preview { flex: 1; overflow-y: auto; min-height: 0; padding-right: 4px; }
            .fact-item { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.04); font-size: 11px; }
            .fact-btn { background: transparent; border: none; color: var(--text-dim); cursor: pointer; font-size: 12px; transition: color 0.2s; }
            .fact-btn:hover { color: var(--accent-cyan); }

            .reasoning-box { background: rgba(0,0,0,0.4); border: 1px solid rgba(0,240,255,0.15); border-radius: 10px; padding: 8px; font-size: 10px; font-family: monospace; color: var(--accent-cyan); flex: 1; overflow-y: auto; }

            .bottom-command-bar { height: 64px; border-top: 1px solid var(--glass-border); padding: 0 24px; display: flex; align-items: center; gap: 16px; background: rgba(6, 9, 19, 0.95); backdrop-filter: blur(20px); flex-shrink: 0; }
            .cmd-input-container { flex: 1; display: flex; align-items: center; background: rgba(15, 23, 42, 0.6); border: 1px solid var(--glass-border); border-radius: 30px; padding: 6px 8px 6px 20px; transition: border-color 0.3s; }
            .cmd-input-container:focus-within { border-color: var(--accent-cyan); box-shadow: 0 0 15px rgba(0,240,255,0.15); }
            .cmd-input { flex: 1; background: transparent; border: none; outline: none; color: #fff; font-size: 13px; }
            .cmd-btn { padding: 10px 24px; background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)); color: #000; border: none; border-radius: 24px; font-weight: 800; font-size: 12px; cursor: pointer; transition: transform 0.2s; }
            .cmd-btn:hover { transform: scale(1.03); }

            #nexus-graph-canvas { width: 100%; height: 100%; display: block; background: #060913; cursor: grab; }
        </style>
    </head>
    <body>
        <header>
            <div class="header-brand"><div class="logo-orb">P</div><div class="header-title">PETER HUD COMMAND CENTER</div></div>
            <div class="sys-badge"><span style="width: 6px; height: 6px; border-radius: 50%; background: var(--accent-green); box-shadow: 0 0 8px var(--accent-green);"></span>PETER AGENT: ONLINE</div>
            <div id="live-clock" class="clock-display">00:00:00</div>
        </header>

        <div class="command-grid">
            <aside class="sidebar-panel">
                <div class="nav-menu">
                    <div class="nav-item active" onclick="switchMainView('hud')">🌐 Dashboard AI</div>
                    <div class="nav-item" onclick="switchMainView('nexus')">🕸️ Nexus 3D Graph</div>
                </div>
                <div class="peter-avatar-card">
                    <canvas id="peter-avatar-canvas" title="Clicca per parlare a voce con Peter"></canvas>
                    <div id="avatar-status-badge" class="avatar-status-tag">STATUS // IDLE</div>
                    <div style="font-size: 10px; color: var(--text-dim);">Clicca per Voice Call</div>
                </div>
            </aside>

            <main class="center-workspace">
                <div id="view-hud" class="view-tab active">
                    <div class="hud-screen">
                        <div class="hud-screen-header">
                            <span>REACTIVE VISUAL HUD</span>
                            <span id="hud-status-badge">STANDBY // CORE</span>
                        </div>
                        <div id="hud-screen-content">
                            <div id="hud-default-overlay" style="text-align: center;">
                                <h2 style="font-size: 20px; font-weight: 900; letter-spacing: 3px; background: linear-gradient(90deg, #fff, var(--accent-cyan)); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">PETER COMPANION CORE</h2>
                            </div>
                        </div>
                    </div>

                    <section class="feed-panel">
                        <div class="panel-header"><span>LIVE DIALOG FEED</span><span style="font-size: 10px; color: var(--accent-green);">● READY</span></div>
                        <div id="chat-feed">
                            <div class="msg peter">Layout fisso e pulito applicato. Dimmi tutto Marco, come procediamo?</div>
                        </div>
                    </section>
                </div>

                <div id="view-nexus" class="view-tab" style="position: relative; overflow: hidden; border-radius: 20px; border: 1px solid var(--glass-border); height: 100%;">
                    <canvas id="nexus-graph-canvas"></canvas>
                </div>
            </main>

            <aside class="right-sidebar">
                <div class="widget-card flex-grow">
                    <div class="panel-header" style="padding: 0 0 10px 0; border: none;">MEMORIA (EDITABLE)</div>
                    <div id="facts-preview">Caricamento memorie...</div>
                </div>
                <div class="widget-card fixed-small">
                    <div class="panel-header" style="padding: 0 0 6px 0; border: none;">REASONING STREAM</div>
                    <div id="reasoning-preview" class="reasoning-box">> In ascolto...</div>
                </div>
            </aside>
        </div>

        <footer class="bottom-command-bar">
            <div class="cmd-input-container">
                <input type="text" id="cmd-input" class="cmd-input" placeholder="Parla con Peter..." autocomplete="off" />
                <button type="button" id="send-cmd-btn" class="cmd-btn">INVIA</button>
            </div>
        </footer>

        <script>
            let currentAvatarState = 'IDLE';

            setInterval(() => {
                document.getElementById('live-clock').innerText = new Date().toTimeString().split(' ')[0];
            }, 1000);

            function switchMainView(view) {
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                document.querySelectorAll('.view-tab').forEach(v => v.classList.remove('active'));
                event.target.classList.add('active');
                if(view === 'hud') document.getElementById('view-hud').classList.add('active');
                else if(view === 'nexus') { document.getElementById('view-nexus').classList.add('active'); loadNexus3D(); }
            }

            (function initPeterAvatar() {
                const canvas = document.getElementById('peter-avatar-canvas');
                const ctx = canvas.getContext('2d');
                let angle = 0;
                function renderAvatar() {
                    ctx.clearRect(0, 0, 130, 130);
                    angle += (currentAvatarState === 'THINKING' ? 0.08 : 0.02);
                    let auraColor = '#00f0ff';
                    if(currentAvatarState === 'SPEAKING') auraColor = '#8b5cf6';
                    if(currentAvatarState === 'LISTENING') auraColor = '#ec4899';
                    if(currentAvatarState === 'THINKING') auraColor = '#f59e0b';
                    document.getElementById('avatar-status-badge').innerText = `STATUS // ${currentAvatarState}`;
                    document.getElementById('avatar-status-badge').style.borderColor = auraColor;

                    let radiusPulse = 38 + Math.sin(angle * 3) * (currentAvatarState === 'SPEAKING' ? 6 : 2);
                    ctx.beginPath(); ctx.arc(65, 65, radiusPulse, 0, Math.PI * 2);
                    ctx.strokeStyle = auraColor; ctx.lineWidth = 2; ctx.stroke();

                    for(let i = 0; i < 3; i++) {
                        ctx.save(); ctx.translate(65, 65); ctx.rotate(angle * (i % 2 === 0 ? 1 : -1) + (i * Math.PI / 3));
                        ctx.beginPath(); ctx.ellipse(0, 0, 28 + i * 5, 10, 0, 0, Math.PI * 2);
                        ctx.strokeStyle = auraColor; ctx.globalAlpha = 0.45; ctx.stroke(); ctx.restore();
                    }
                    ctx.beginPath(); ctx.arc(65, 65, 12 + Math.cos(angle * 2) * 2, 0, Math.PI * 2);
                    ctx.fillStyle = auraColor; ctx.shadowBlur = 15; ctx.shadowColor = auraColor; ctx.fill(); ctx.shadowBlur = 0;
                    requestAnimationFrame(renderAvatar);
                }
                renderAvatar();
                canvas.onclick = toggleVoiceSession;
            })();

            function updateHudScreen(screen) {
                const container = document.getElementById('hud-screen-content');
                const badge = document.getElementById('hud-status-badge');
                if(!screen || screen.type === 'NONE') return;
                badge.innerText = `ACTIVE DISPLAY // ${screen.type}`;

                if(screen.type === 'WEB_BROWSER' && screen.url) {
                    container.innerHTML = `
                        <div style="width:100%; max-width:400px; background:rgba(15,23,42,0.95); border:1px solid var(--accent-cyan); border-radius:14px; padding:16px; display:flex; flex-direction:column; gap:10px; text-align:center;">
                            <div style="font-size:28px;">🌐</div>
                            <h3 style="color:var(--accent-cyan); font-size:13px; word-break:break-all;">${screen.url}</h3>
                            <p style="font-size:10px; color:var(--text-dim);">Navigazione sicura via LinkViewer Card.</p>
                            <a href="${screen.url}" target="_blank" style="background:linear-gradient(135deg, var(--accent-cyan), var(--accent-purple)); color:#000; text-decoration:none; padding:8px 14px; border-radius:8px; font-weight:800; font-size:11px; display:inline-block;">Apri Pagina Web ↗</a>
                        </div>
                    `;
                } 
                else if(screen.type === 'MEDIA_PLAYER') {
                    let embedLink = screen.embed_url;
                    if(embedLink && embedLink.includes('watch?v=')) {
                        const vidId = embedLink.split('watch?v=')[1]?.substring(0, 11);
                        if(vidId) embedLink = `https://www.youtube-nocookie.com/embed/${vidId}?autoplay=1`;
                    }
                    
                    container.innerHTML = `
                        <div style="width:100%; height:100%; display:flex; flex-direction:column; gap:8px; justify-content:center; align-items:center;">
                            <div style="width:100%; max-width:400px; aspect-ratio:16/9; border-radius:10px; overflow:hidden; border:1px solid var(--accent-cyan); background:#000;">
                                <iframe src="${embedLink}" style="width:100%; height:100%; border:none;" allow="accelerometer; autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>
                            </div>
                            ${screen.watch_url ? `<a href="${screen.watch_url}" target="_blank" style="color:var(--accent-cyan); font-size:11px; text-decoration:none; background:rgba(0,240,255,0.08); padding:4px 10px; border-radius:6px; border:1px solid rgba(0,240,255,0.2);">🔗 Apri video su YouTube</a>` : ''}
                        </div>
                    `;
                } 
                else if(screen.type === 'PERSON_CARD' && screen.person) {
                    container.innerHTML = `<div style="background:rgba(15,23,42,0.95); border:1px solid var(--accent-cyan); padding:16px; border-radius:14px; text-align:center; max-width:280px;"><div style="font-size:30px; margin-bottom:2px;">👤</div><h3 style="color:var(--accent-cyan); font-size:16px;">${screen.person.name}</h3><p style="font-size:10px; color:var(--text-dim); margin-bottom:6px;">Livello: ${screen.person.category}</p><p style="font-size:11px; line-height:1.3;">${screen.person.notes || 'In Nexus'}</p></div>`;
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
                        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text })
                    });
                    const data = await res.json();
                    if(data.reply) {
                        appendMsg(data.reply, 'peter');
                        if(data.screen) updateHudScreen(data.screen);
                        if(data.reasoning) document.getElementById('reasoning-preview').innerText = data.reasoning;
                        currentAvatarState = 'IDLE';
                        loadBrainSummary();
                    }
                } catch(e) {
                    appendMsg("Errore connessione.", "peter");
                    currentAvatarState = 'IDLE';
                }
            }
            btn.onclick = sendMessage;
            input.onkeypress = (e) => { if(e.key === 'Enter') sendMessage(); };

            function appendMsg(text, sender) {
                const div = document.createElement('div');
                div.className = `msg ${sender}`; div.innerText = text;
                feed.appendChild(div); feed.scrollTop = feed.scrollHeight;
            }

            async function loadBrainSummary() {
                try {
                    const res = await fetch('/memories');
                    const data = await res.json();
                    if(data.connected && data.long_term_facts) {
                        document.getElementById('facts-preview').innerHTML = data.long_term_facts.map(f => `
                            <div class="fact-item"><span id="fact-text-${f.id}">🧠 ${f.fact}</span>
                            <div style="display:flex; gap:4px;">
                                <button class="fact-btn" onclick="editFact('${f.id}', '${f.fact.replace(/'/g, "\\'")}')">✏️</button>
                                <button class="fact-btn" onclick="deleteFact('${f.id}')">🗑️</button>
                            </div></div>`).join('');
                    }
                } catch(e){}
            }

            async function editFact(id, oldText) {
                const newText = prompt("Modifica:", oldText);
                if(newText && newText !== oldText) {
                    await fetch(`/api/facts/${id}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ fact: newText }) });
                    loadBrainSummary();
                }
            }

            async function deleteFact(id) {
                if(confirm("Eliminare?")) {
                    await fetch(`/api/facts/${id}`, { method: 'DELETE' });
                    loadBrainSummary();
                }
            }

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
                            if(data.reasoning) document.getElementById('reasoning-preview').innerText = data.reasoning;
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

            loadBrainSummary();
        </script>
    </body>
    </html>
    """
