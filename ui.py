def get_dashboard_html() -> str:
    return """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PETER HUD OS v10 - True 3D Nexus & Settings</title>
        
        <!-- Importiamo la libreria per il VERO GRAFO 3D -->
        <script src="https://unpkg.com/3d-force-graph"></script>

        <style>
            :root { 
                --bg-main: #04060d; 
                --panel-bg: rgba(10, 17, 32, 0.85); 
                --glass-border: rgba(0, 240, 255, 0.22); 
                --accent-cyan: #00f0ff; 
                --accent-purple: #8b5cf6; 
                --accent-green: #10b981; 
                --accent-pink: #ec4899;
                --accent-yellow: #f59e0b;
                --accent-red: #ef4444;
                --text-bright: #f8fafc; 
                --text-dim: #94a3b8; 
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: "Inter", sans-serif; }
            body { background: radial-gradient(circle at 50% 20%, #0c162d 0%, #04060d 100%); color: var(--text-bright); height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
            
            header { height: 56px; border-bottom: 1px solid var(--glass-border); padding: 0 24px; display: flex; align-items: center; justify-content: space-between; background: rgba(4, 6, 13, 0.92); backdrop-filter: blur(20px); z-index: 100; flex-shrink: 0; }
            .header-brand { display: flex; align-items: center; gap: 12px; }
            .logo-orb { width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple)); display: flex; align-items: center; justify-content: center; box-shadow: 0 0 20px rgba(0, 240, 255, 0.5); font-weight: 900; font-size: 13px; color: #000; }
            .header-title { font-size: 13px; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; background: linear-gradient(90deg, #fff, var(--accent-cyan)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            
            .sys-badge { display: flex; align-items: center; gap: 8px; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3); padding: 4px 14px; border-radius: 30px; font-size: 11px; color: var(--accent-green); font-weight: 600; letter-spacing: 1px; }
            .clock-display { font-family: monospace; font-size: 14px; color: var(--accent-cyan); letter-spacing: 2px; }

            .command-grid { flex: 1; display: grid; grid-template-columns: 260px 1fr 340px; gap: 16px; padding: 16px; height: calc(100vh - 120px); overflow: hidden; }

            /* SIDEBAR NAZIGAZIONE */
            .sidebar-panel { background: var(--panel-bg); border: 1px solid var(--glass-border); border-radius: 20px; padding: 18px; display: flex; flex-direction: column; gap: 16px; backdrop-filter: blur(24px); box-shadow: 0 8px 32px rgba(0,0,0,0.4); height: 100%; overflow: hidden; }
            .nav-menu { display: flex; flex-direction: column; gap: 8px; }
            .nav-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 12px; font-size: 12px; font-weight: 600; color: var(--text-dim); cursor: pointer; transition: all 0.25s ease; }
            .nav-item.active, .nav-item:hover { background: linear-gradient(90deg, rgba(0, 240, 255, 0.15), transparent); color: var(--accent-cyan); border-left: 3px solid var(--accent-cyan); transform: translateX(2px); }

            .peter-avatar-card { background: rgba(0,0,0,0.5); border: 1px solid var(--glass-border); border-radius: 16px; padding: 14px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 8px; flex-shrink: 0; }
            #peter-avatar-canvas { width: 130px; height: 130px; border-radius: 50%; cursor: pointer; }
            .avatar-status-tag { font-size: 9px; font-family: monospace; letter-spacing: 1.5px; color: var(--accent-cyan); background: rgba(0,240,255,0.1); padding: 3px 10px; border-radius: 12px; border: 1px solid rgba(0,240,255,0.3); }

            .center-workspace { display: flex; flex-direction: column; gap: 16px; height: 100%; overflow: hidden; }
            
            /* TABS */
            .view-tab { display: none; flex-direction: column; gap: 16px; height: 100%; width: 100%; overflow: hidden; }
            .view-tab.active { display: flex; }

            /* HUD E CHAT (DASHBOARD) */
            .hud-screen { background: var(--panel-bg); border: 1px solid var(--glass-border); border-radius: 20px; height: 280px; flex-shrink: 0; position: relative; overflow: hidden; display: flex; flex-direction: column; backdrop-filter: blur(20px); }
            .hud-screen-header { padding: 8px 16px; background: rgba(0,0,0,0.3); border-bottom: 1px solid var(--glass-border); font-size: 10px; font-family: monospace; color: var(--accent-cyan); display: flex; justify-content: space-between; flex-shrink: 0; }
            #hud-screen-content { flex: 1; padding: 12px; overflow: hidden; display: flex; align-items: center; justify-content: center; position: relative; }

            .feed-panel { background: var(--panel-bg); border: 1px solid var(--glass-border); border-radius: 20px; flex: 1; display: flex; flex-direction: column; overflow: hidden; backdrop-filter: blur(20px); min-height: 0; }
            .panel-header { padding: 10px 16px; border-bottom: 1px solid var(--glass-border); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--accent-cyan); display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
            
            #chat-feed { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 10px; scroll-behavior: smooth; min-height: 0; }
            .msg { max-width: 80%; padding: 10px 14px; border-radius: 14px; font-size: 13px; line-height: 1.45; word-wrap: break-word; flex-shrink: 0; }
            .msg.user { align-self: flex-end; background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue)); color: #fff; border-bottom-right-radius: 4px; box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3); }
            .msg.peter { align-self: flex-start; background: rgba(15, 23, 42, 0.85); border: 1px solid var(--glass-border); border-bottom-left-radius: 4px; }
            
            /* RIGHT SIDEBAR (MEMORIE) */
            .right-sidebar { display: flex; flex-direction: column; gap: 16px; height: 100%; overflow: hidden; }
            .widget-card { background: var(--panel-bg); border: 1px solid var(--glass-border); border-radius: 20px; padding: 16px; backdrop-filter: blur(20px); box-shadow: 0 8px 32px rgba(0,0,0,0.4); display: flex; flex-direction: column; overflow: hidden; }
            .widget-card.flex-grow { flex: 1; min-height: 0; }
            .widget-card.fixed-small { height: 160px; flex-shrink: 0; }
            
            #facts-preview { flex: 1; overflow-y: auto; min-height: 0; padding-right: 4px; }
            .fact-item { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 11px; }
            .fact-btn { background: transparent; border: none; color: var(--text-dim); cursor: pointer; font-size: 12px; transition: color 0.2s; }
            .fact-btn:hover { color: var(--accent-cyan); }

            .reasoning-box { background: rgba(0,0,0,0.5); border: 1px solid rgba(0,240,255,0.2); border-radius: 10px; padding: 8px; font-size: 10px; font-family: monospace; color: var(--accent-cyan); flex: 1; overflow-y: auto; }

            /* COMMAND BAR INFERIORE */
            .bottom-command-bar { height: 64px; border-top: 1px solid var(--glass-border); padding: 0 24px; display: flex; align-items: center; gap: 12px; background: rgba(4, 6, 13, 0.95); backdrop-filter: blur(20px); flex-shrink: 0; }
            .cmd-input-container { flex: 1; display: flex; align-items: center; background: rgba(15, 23, 42, 0.7); border: 1px solid var(--glass-border); border-radius: 30px; padding: 4px 8px 4px 16px; transition: border-color 0.3s; gap: 8px; }
            .cmd-input-container:focus-within { border-color: var(--accent-cyan); box-shadow: 0 0 15px rgba(0,240,255,0.2); }
            .cmd-input { flex: 1; background: transparent; border: none; outline: none; color: #fff; font-size: 13px; }
            .file-upload-btn { background: transparent; border: none; color: var(--text-dim); cursor: pointer; font-size: 16px; transition: color 0.2s; }
            .file-upload-btn:hover { color: var(--accent-cyan); }
            .cmd-btn { padding: 10px 20px; background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple)); color: #000; border: none; border-radius: 24px; font-weight: 800; font-size: 12px; cursor: pointer; transition: transform 0.2s; }
            .cmd-btn:hover { transform: scale(1.03); }

            /* VERO 3D NEXUS GRAPH */
            #nexus-3d-container { width: 100%; height: 100%; border-radius: 20px; border: 1px solid var(--glass-border); overflow: hidden; position: relative; }
            .nexus-toolbar { position: absolute; top: 16px; left: 16px; display: flex; gap: 6px; z-index: 10; background: rgba(10,17,32,0.9); padding: 8px 12px; border-radius: 12px; border: 1px solid var(--glass-border); backdrop-filter: blur(12px); flex-wrap: wrap; }
            .nexus-filter-btn { background: rgba(0,240,255,0.1); border: 1px solid rgba(0,240,255,0.3); color: var(--text-bright); padding: 5px 12px; border-radius: 8px; font-size: 10px; font-weight: 700; cursor: pointer; transition: all 0.2s; }
            .nexus-filter-btn.active, .nexus-filter-btn:hover { background: var(--accent-cyan); color: #000; box-shadow: 0 0 12px rgba(0,240,255,0.5); }
            
            .nexus-inspector { position: absolute; bottom: 16px; right: 16px; width: 300px; background: rgba(10,17,32,0.96); border: 1px solid var(--accent-cyan); border-radius: 14px; padding: 16px; display: none; z-index: 10; backdrop-filter: blur(18px); box-shadow: 0 10px 30px rgba(0,0,0,0.7); }

            /* SETTINGS TAB */
            .settings-container { padding: 24px; background: var(--panel-bg); border: 1px solid var(--glass-border); border-radius: 20px; height: 100%; overflow-y: auto; }
            .settings-group { margin-bottom: 24px; padding-bottom: 24px; border-bottom: 1px solid rgba(255,255,255,0.05); }
            .settings-group h3 { color: var(--accent-cyan); font-size: 14px; text-transform: uppercase; margin-bottom: 12px; letter-spacing: 1px; }
            .settings-label { font-size: 12px; color: var(--text-dim); margin-bottom: 4px; display: block; }
            .settings-input { width: 100%; background: rgba(0,0,0,0.3); border: 1px solid var(--glass-border); color: #fff; padding: 10px; border-radius: 8px; font-size: 13px; margin-bottom: 12px; }
            .danger-btn { background: rgba(239, 68, 68, 0.1); border: 1px solid var(--accent-red); color: var(--accent-red); padding: 10px 16px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 12px; transition: all 0.2s; margin-right: 8px; }
            .danger-btn:hover { background: var(--accent-red); color: #000; box-shadow: 0 0 15px rgba(239, 68, 68, 0.4); }

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
                    <div class="nav-item" onclick="switchMainView('nexus')">🕸️ True 3D Nexus</div>
                    <div class="nav-item" onclick="switchMainView('settings')">⚙️ Settings & Data</div>
                </div>
                <div class="peter-avatar-card">
                    <canvas id="peter-avatar-canvas" title="Clicca per parlare a voce con Peter"></canvas>
                    <div id="avatar-status-badge" class="avatar-status-tag">STATUS // IDLE</div>
                    <div style="font-size: 10px; color: var(--text-dim);">Clicca per Voice Call</div>
                </div>
            </aside>

            <main class="center-workspace">
                
                <!-- TAB 1: DASHBOARD -->
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
                            <div class="msg peter">Sistema Aggiornato alla v10. Moduli 3D WebGL pronti.</div>
                        </div>
                    </section>
                </div>

                <!-- TAB 2: IL VERO NEXUS 3D -->
                <div id="view-nexus" class="view-tab" style="position: relative; height: 100%;">
                    <div class="nexus-toolbar">
                        <button class="nexus-filter-btn active" onclick="filterNexusLayer3D('all', this)">TUTTO</button>
                        <button class="nexus-filter-btn" onclick="filterNexusLayer3D('person', this)">👥 Persone</button>
                        <button class="nexus-filter-btn" onclick="filterNexusLayer3D('memory', this)">🧠 Memorie</button>
                        <button class="nexus-filter-btn" onclick="filterNexusLayer3D('event', this)">📅 Eventi</button>
                        <button class="nexus-filter-btn" onclick="filterNexusLayer3D('interest', this)">⚡ Interessi</button>
                    </div>
                    
                    <!-- Container dove WebGL inietterà il Canvas -->
                    <div id="nexus-3d-container"></div>
                    
                    <div id="nexus-inspector" class="nexus-inspector">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <span id="inspector-type" style="font-size:9px; font-family:monospace; color:var(--accent-cyan); text-transform:uppercase;">NODO</span>
                            <span onclick="document.getElementById('nexus-inspector').style.display='none'" style="cursor:pointer; font-size:14px; color:var(--text-dim);">✕</span>
                        </div>
                        <h4 id="inspector-title" style="font-size:15px; color:#fff; margin-bottom:6px;">Nome</h4>
                        <p id="inspector-desc" style="font-size:11px; color:var(--text-dim); line-height:1.45; word-break:break-word;">Dettagli...</p>
                    </div>
                </div>

                <!-- TAB 3: SETTINGS & DANGER ZONE -->
                <div id="view-settings" class="view-tab">
                    <div class="settings-container">
                        <div class="settings-group">
                            <h3>Impostazioni Personalità (WIP)</h3>
                            <label class="settings-label">Tone of Voice (Come Peter si rivolge a te)</label>
                            <input type="text" class="settings-input" id="setting-tone" value="Schietto, empatico, naturale, colto e ironico.">
                            <button class="nexus-filter-btn" onclick="alert('Salvataggio impostazioni in arrivo...')">Salva Personalità</button>
                        </div>
                        
                        <div class="settings-group">
                            <h3 style="color: var(--accent-red);">Danger Zone (Pulizia Database)</h3>
                            <p style="font-size:11px; color:var(--text-dim); margin-bottom:12px;">Queste azioni elimineranno permanentemente i dati da Supabase.</p>
                            <button class="danger-btn" onclick="wipeData('memories')">Svuota Chat</button>
                            <button class="danger-btn" onclick="wipeData('contacts')">Cancella Persone</button>
                            <button class="danger-btn" onclick="wipeData('events')">Cancella Eventi</button>
                            <button class="danger-btn" onclick="wipeData('all')">WIPE TOTALE (Hard Reset)</button>
                        </div>
                    </div>
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
                <input type="file" id="file-input" style="display:none" accept="image/*" />
                <button type="button" class="file-upload-btn" onclick="document.getElementById('file-input').click()" title="Allega immagine">📎</button>
                <input type="text" id="cmd-input" class="cmd-input" placeholder="Parla con Peter o carica un'immagine..." autocomplete="off" />
                <button type="button" id="send-cmd-btn" class="cmd-btn">INVIA</button>
            </div>
        </footer>

        <script>
            let currentAvatarState = 'IDLE';
            let attachedFile = null;
            let Graph = null; // L'oggetto 3D Force Graph
            let graphDataCache = { nodes: [], links: [] };

            document.getElementById('file-input').onchange = (e) => {
                attachedFile = e.target.files[0];
                if(attachedFile) {
                    document.getElementById('cmd-input').placeholder = `Immagine allegata: ${attachedFile.name}`;
                }
            };

            setInterval(() => {
                document.getElementById('live-clock').innerText = new Date().toTimeString().split(' ')[0];
            }, 1000);

            function switchMainView(view) {
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                document.querySelectorAll('.view-tab').forEach(v => v.classList.remove('active'));
                event.target.classList.add('active');
                if(view === 'hud') document.getElementById('view-hud').classList.add('active');
                else if(view === 'settings') document.getElementById('view-settings').classList.add('active');
                else if(view === 'nexus') { 
                    document.getElementById('view-nexus').classList.add('active'); 
                    initOrRefresh3DGraph(); 
                }
            }

            // --- INIZIO LOGICA AVATAR E CHAT ---
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
            })();

            const input = document.getElementById('cmd-input');
            const btn = document.getElementById('send-cmd-btn');
            const feed = document.getElementById('chat-feed');

            async function sendMessage() {
                const text = input.value.trim();
                if(!text && !attachedFile) return;
                appendMsg(text || '[Immagine allegata]', 'user');
                input.value = '';
                currentAvatarState = 'THINKING';

                const formData = new FormData();
                formData.append('message', text);
                if(attachedFile) {
                    formData.append('file', attachedFile);
                    attachedFile = null;
                    document.getElementById('cmd-input').placeholder = "Parla con Peter o carica un'immagine...";
                }

                try {
                    const res = await fetch('/chat', {
                        method: 'POST', body: formData
                    });
                    const data = await res.json();
                    if(data.reply) {
                        appendMsg(data.reply, 'peter');
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
                                <button class="fact-btn" onclick="deleteFact('${f.id}')">🗑️</button>
                            </div></div>`).join('');
                    }
                } catch(e){}
            }

            async function deleteFact(id) {
                if(confirm("Eliminare la memoria?")) {
                    await fetch(`/api/facts/${id}`, { method: 'DELETE' });
                    loadBrainSummary();
                }
            }
            // --- FINE LOGICA BASE ---

            // --- INIZIO MOTORE 3D WEBGL (FORCE GRAPH) ---
            async function fetchGraphData() {
                try {
                    const res = await fetch('/api/nexus');
                    const data = await res.json();
                    
                    // Convertiamo i dati in formato accettato da 3d-force-graph
                    // Il motore WebGL ricalcola autonomamente x, y, z in base alle forze, ma partiamo dai dati che abbiamo.
                    graphDataCache = {
                        nodes: data.nodes.map(n => ({ id: n.id, name: n.name, type: n.type, val: n.type==='core'? 10 : 3, ...n })),
                        links: data.edges.map(e => ({ source: e.source, target: e.target, relation: e.relation_type || 'neutro' }))
                    };
                    return graphDataCache;
                } catch (e) {
                    console.error("Errore fetch grafo:", e);
                    return {nodes:[], links:[]};
                }
            }

            function getNodeColor(node) {
                if (node.type === 'core') return '#10b981'; // Verde
                if (node.type === 'person') {
                    // Colore per sesso
                    if(node.gender && node.gender.toUpperCase() === 'M') return '#3b82f6'; // Blu uomo
                    if(node.gender && node.gender.toUpperCase() === 'F') return '#ec4899'; // Rosa donna
                    return '#00f0ff'; // Ciano default
                }
                if (node.type === 'memory') return '#8b5cf6'; // Viola
                if (node.type === 'event') return '#f43f5e'; // Rosso tenue
                if (node.type === 'interest') return '#f59e0b'; // Ambra
                return '#ffffff';
            }

            function getLinkColor(link) {
                let rel = link.relation || '';
                rel = rel.toLowerCase();
                if(rel.includes('amore') || rel.includes('fidanzat')) return 'rgba(236, 72, 153, 0.6)'; // Rosa
                if(rel.includes('famiglia') || rel.includes('parent')) return 'rgba(16, 185, 129, 0.6)'; // Verde
                if(rel.includes('lavoro')) return 'rgba(245, 158, 11, 0.6)'; // Ambra
                return 'rgba(0, 240, 255, 0.2)'; // Standard Cyan
            }

            async function initOrRefresh3DGraph() {
                const container = document.getElementById('nexus-3d-container');
                if (!container) return;

                const data = await fetchGraphData();

                if (!Graph) {
                    // Inizializza WebGL Graph
                    Graph = ForceGraph3D()(container)
                        .backgroundColor('#04060d')
                        .showNavInfo(false)
                        .nodeResolution(16)
                        .nodeRelSize(4)
                        .nodeColor(getNodeColor)
                        .linkColor(getLinkColor)
                        .linkOpacity(0.5)
                        .linkWidth(1)
                        .nodeLabel('name') // Tooltip base in hover
                        .onNodeClick(node => {
                            // Mostra Inspector
                            showInspector(node);
                            // Centra e zooma sulla camera
                            const distance = 80;
                            const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);
                            Graph.cameraPosition(
                                { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }, 
                                node, // LookAt
                                1500  // Transition ms
                            );
                        });
                }
                
                Graph.graphData(data);
                
                // Distribuzione personalizzata lungo l'asse Y per le persone (Età)
                Graph.d3Force('y', d3.forceY().y(node => {
                    if(node.type === 'person' && node.birth_year) {
                        // Più vecchi in alto (es. y negativa), più giovani in basso
                        const currentYear = 2026;
                        const age = currentYear - parseInt(node.birth_year);
                        return (age - 30) * -5; // Spread basato sull'età
                    }
                    return 0;
                }).strength(0.1));
            }

            function filterNexusLayer3D(layer, btn) {
                document.querySelectorAll('.nexus-filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                if (!Graph) return;

                const filteredData = {
                    nodes: graphDataCache.nodes.filter(n => layer === 'all' || n.type === layer || n.type === 'core'),
                    links: graphDataCache.links.filter(l => {
                        const sourceMatch = (layer === 'all' || l.source.type === layer || l.source.type === 'core');
                        const targetMatch = (layer === 'all' || l.target.type === layer || l.target.type === 'core');
                        return sourceMatch && targetMatch;
                    })
                };
                
                Graph.graphData(filteredData);
            }

            function showInspector(node) {
                const inspector = document.getElementById('nexus-inspector');
                document.getElementById('inspector-type').innerText = `LAYER // ${node.type.toUpperCase()}`;
                
                let title = node.name;
                // Aggiungi indicatori visivi nel titolo dell'inspector
                if(node.type === 'person') {
                    if(node.gender === 'M') title += " ♂️";
                    if(node.gender === 'F') title += " ♀️";
                    if(node.birth_year) title += ` (Nato: ${node.birth_year})`;
                }
                
                document.getElementById('inspector-title').innerText = title;
                
                let desc = `${node.notes || ''} \n\n${node.details || ''}`;
                if(node.relation_type && node.relation_type !== 'neutrale') {
                    desc += `\nLegame: ${node.relation_type.toUpperCase()}`;
                }
                
                document.getElementById('inspector-desc').innerText = desc.trim();
                inspector.style.display = 'block';
            }
            // --- FINE MOTORE 3D ---

            async function wipeData(type) {
                if(confirm(`Sei SICURO di voler eliminare i dati di tipo: ${type}? L'azione è IRREVERSIBILE.`)) {
                    try {
                        const res = await fetch(`/api/wipe/${type}`, { method: 'DELETE' });
                        if(res.ok) {
                            alert("Dati eliminati con successo.");
                            loadBrainSummary();
                            initOrRefresh3DGraph();
                        } else {
                            alert("Errore nell'eliminazione.");
                        }
                    } catch(e) {
                        alert("Errore di rete.");
                    }
                }
            }

            loadBrainSummary();
        </script>
    </body>
    </html>
    """
