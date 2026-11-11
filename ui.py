def get_dashboard_html() -> str:
    return """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Peter OS - JARVIS HUD</title>
        <style>
            :root {
                --bg-core: #04070c;
                --panel-bg: rgba(10, 16, 26, 0.75);
                --border-neon: rgba(0, 240, 255, 0.2);
                --accent-cyan: #00f0ff;
                --accent-blue: #2563eb;
                --text-main: #f0f6fc;
                --text-dim: #8b949e;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            body { background: var(--bg-core); color: var(--text-main); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
            
            /* Top Sci-Fi Header */
            header { height: 60px; border-bottom: 1px solid var(--border-neon); padding: 0 24px; display: flex; align-items: center; justify-content: space-between; background: rgba(4, 7, 12, 0.9); backdrop-filter: blur(12px); }
            .brand { display: flex; align-items: center; gap: 12px; }
            .brand-glow { width: 12px; height: 12px; background: var(--accent-cyan); border-radius: 50%; box-shadow: 0 0 12px var(--accent-cyan); }
            .brand h1 { font-size: 16px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #fff; }
            
            .nav-tabs { display: flex; gap: 8px; background: rgba(15, 23, 42, 0.6); padding: 4px; border-radius: 12px; border: 1px solid var(--border-neon); }
            .tab-btn { background: transparent; border: none; color: var(--text-dim); padding: 8px 16px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s; letter-spacing: 0.5px; }
            .tab-btn.active { background: var(--accent-blue); color: #fff; box-shadow: 0 0 10px rgba(37, 99, 235, 0.5); }

            .sys-metrics { display: flex; gap: 16px; font-size: 11px; color: var(--text-dim); font-family: monospace; }
            .metric-pill { background: rgba(15, 23, 42, 0.8); padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05); }

            /* Main Dashboard Grid */
            .main-container { flex: 1; height: calc(100vh - 60px); overflow: hidden; position: relative; }
            .tab-content { display: none; height: 100%; width: 100%; }
            .tab-content.active { display: flex; }

            /* Tab 1: JARVIS Core Chat */
            .hud-grid { display: grid; grid-template-columns: 1fr 380px; width: 100%; height: 100%; }
            @media (max-width: 950px) { .hud-grid { grid-template-columns: 1fr; } .hud-sidebar { display: none; } }

            .hud-main { display: flex; flex-direction: column; height: 100%; background: radial-gradient(circle at top left, rgba(0,240,255,0.03), transparent 40%); border-right: 1px solid var(--border-neon); }
            #chat-container { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; }
            
            .msg { max-width: 82%; padding: 14px 18px; border-radius: 16px; font-size: 14px; line-height: 1.55; word-wrap: break-word; backdrop-filter: blur(8px); }
            .msg.user { align-self: flex-end; background: linear-gradient(135deg, #1e40af, #2563eb); color: #fff; border-bottom-right-radius: 4px; box-shadow: 0 4px 14px rgba(37,99,235,0.3); }
            .msg.peter { align-self: flex-start; background: var(--panel-bg); color: var(--text-main); border: 1px solid var(--border-neon); border-bottom-left-radius: 4px; }
            
            .tool-badge { font-size: 11px; font-family: monospace; color: var(--accent-cyan); background: rgba(0, 240, 255, 0.1); border: 1px solid var(--border-neon); padding: 4px 8px; border-radius: 6px; margin-bottom: 8px; display: inline-block; }
            .media-box { margin-top: 12px; border-radius: 12px; overflow: hidden; border: 1px solid var(--border-neon); background: #000; box-shadow: 0 0 20px rgba(0,240,255,0.15); }
            .media-box iframe { width: 100%; height: 220px; border: none; }
            .typing { font-style: italic; color: var(--accent-cyan); font-size: 12px; font-family: monospace; }

            .chat-footer { padding: 16px 24px; border-top: 1px solid var(--border-neon); background: rgba(4, 7, 12, 0.95); }
            form { display: flex; gap: 12px; }
            input { flex: 1; padding: 14px 20px; background: rgba(15, 23, 42, 0.8); border: 1px solid var(--border-neon); border-radius: 28px; color: #fff; font-size: 14px; outline: none; }
            input:focus { border-color: var(--accent-cyan); box-shadow: 0 0 12px rgba(0,240,255,0.3); }
            button.send-btn { padding: 14px 26px; background: var(--accent-cyan); color: #000; border: none; border-radius: 28px; font-weight: 700; cursor: pointer; transition: all 0.2s; letter-spacing: 0.5px; }
            button.send-btn:hover { box-shadow: 0 0 16px var(--accent-cyan); }

            /* Sidebar Widgets */
            .hud-sidebar { padding: 20px; background: var(--bg-core); display: flex; flex-direction: column; gap: 18px; overflow-y: auto; }
            .card { background: var(--panel-bg); border: 1px solid var(--border-neon); border-radius: 14px; padding: 18px; backdrop-filter: blur(10px); }
            .card-title { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: var(--accent-cyan); margin-bottom: 12px; display: flex; justify-content: space-between; }
            .fact-item { font-size: 12px; color: var(--text-main); padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }

            /* Settings Tab */
            .settings-container { padding: 32px; width: 100%; max-width: 900px; margin: 0 auto; overflow-y: auto; display: flex; flex-direction: column; gap: 24px; }
            .setting-row { background: var(--panel-bg); border: 1px solid var(--border-neon); border-radius: 12px; padding: 20px; display: flex; justify-content: space-between; align-items: center; }
            .setting-info h3 { font-size: 15px; font-weight: 600; margin-bottom: 4px; }
            .setting-info p { font-size: 12px; color: var(--text-dim); }
            .setting-input { padding: 10px 14px; background: rgba(15, 23, 42, 0.9); border: 1px solid var(--border-neon); border-radius: 8px; color: #fff; width: 280px; font-size: 13px; }
        </style>
    </head>
    <body>
        <header>
            <div class="brand">
                <div class="brand-glow"></div>
                <h1>Peter JARVIS OS</h1>
            </div>
            
            <div class="nav-tabs">
                <button class="tab-btn active" onclick="switchTab('chat')">⚡ JARVIS Core</button>
                <button class="tab-btn" onclick="switchTab('vault')">🧠 Cervello & Memoria</button>
                <button class="tab-btn" onclick="switchTab('graph')">🕸️ Nexus 3D</button>
                <button class="tab-btn" onclick="switchTab('settings')">⚙️ Impostazioni</button>
            </div>

            <div class="sys-metrics">
                <div class="metric-pill">GROQ: GPT-OSS 120B</div>
                <div class="metric-pill">SUPABASE: ONLINE</div>
            </div>
        </header>

        <div class="main-container">
            <!-- TAB 1: JARVIS CHAT -->
            <div id="tab-chat" class="tab-content active">
                <div class="hud-grid">
                    <section class="hud-main">
                        <div id="chat-container">
                            <div class="msg peter">Sistemi operativi, Marco. Player YouTube, Apple Music e moduli web attivi. Di cosa ci occupiamo?</div>
                        </div>
                        <div class="chat-footer">
                            <form id="chat-form">
                                <input type="text" id="user-input" placeholder="Comanda a Peter o chiedi un video/brano..." autocomplete="off" required />
                                <button type="submit" class="send-btn">ESEGUI</button>
                            </form>
                        </div>
                    </section>

                    <aside class="hud-sidebar">
                        <div class="card">
                            <div class="card-title">MEMORIA ATTIVA <span id="fact-count">0</span></div>
                            <div id="facts-summary">Sincronizzazione dati...</div>
                        </div>
                        <div class="card">
                            <div class="card-title">LIVE MEDIA HUB</div>
                            <div id="active-media-preview" style="font-size: 12px; color: var(--text-dim);">Nessun player attivo.</div>
                        </div>
                    </aside>
                </div>
            </div>

            <!-- TAB 2: MEMORIA VAULT -->
            <div id="tab-vault" class="tab-content">
                <div style="padding: 24px; width: 100%; overflow-y: auto;">
                    <h2 style="margin-bottom: 16px;">Archivio Memoria Concettuale (`user_facts`)</h2>
                    <div id="vault-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px;"></div
                ></div>
            </div>

            <!-- TAB 3: NEXUS GRAPH -->
            <div id="tab-graph" class="tab-content">
                <div style="width: 100%; height: 100%; padding: 20px; display: flex; flex-direction: column;">
                    <h2 style="margin-bottom: 12px;">Grafo Concettuale Entità (Nexus)</h2>
                    <canvas id="graph-canvas" style="flex: 1; background: var(--panel-bg); border: 1px solid var(--border-neon); border-radius: 12px;"></canvas>
                </div>
            </div>

            <!-- TAB 4: IMPOSTAZIONI & TELEGRAM -->
            <div id="tab-settings" class="tab-content">
                <div class="settings-container">
                    <h2>Impostazioni Sistema & Integrazioni</h2>
                    
                    <div class="setting-row">
                        <div class="setting-info">
                            <h3>Telegram Bot Token</h3>
                            <p>Inserisci il Token del bot ottenuto da @BotFather per attivare la chat da mobile.</p>
                        </div>
                        <input type="text" id="telegram-token-input" class="setting-input" placeholder="Es. 123456789:ABC..." />
                    </div>

                    <div class="setting-row">
                        <div class="setting-info">
                            <h3>Registro Webhook Telegram</h3>
                            <p>Associa l'URL di Render (`https://peter-backend-vgnb.onrender.com/telegram/webhook`).</p>
                        </div>
                        <button class="send-btn" style="padding: 10px 18px;" onclick="registerTelegramWebhook()">Registra Webhook</button>
                    </div>

                    <div class="setting-row">
                        <div class="setting-info">
                            <h3>Resetta Memoria Temporanea</h3>
                            <p>Svuota il contesto recente di lavoro in caso di risposte ridondanti.</p>
                        </div>
                        <button style="background:#ef4444; color:#fff; border:none; padding:10px 18px; border-radius:8px; cursor:pointer;" onclick="alert('Memoria di lavoro azzerata.')">Azzera Memoria</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function switchTab(tabId) {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                event.target.classList.add('active');
                document.getElementById(`tab-${tabId}`).classList.add('active');

                if(tabId === 'vault') loadVaultData();
                if(tabId === 'graph') drawNexusGraph();
            }

            const form = document.getElementById('chat-form');
            const input = document.getElementById('user-input');
            const container = document.getElementById('chat-container');
            const factsSummary = document.getElementById('facts-summary');
            const factCount = document.getElementById('fact-count');

            async function loadBrainSummary() {
                try {
                    const res = await fetch('/memories');
                    const data = await res.json();
                    if(data.connected && data.long_term_facts) {
                        factCount.innerText = data.long_term_facts.length;
                        factsSummary.innerHTML = data.long_term_facts.slice(0, 5).map(f => `
                            <div class="fact-item">🧠 ${f.fact}</div>
                        `).join('');
                    }
                } catch(e) {}
            }

            async function loadVaultData() {
                const grid = document.getElementById('vault-grid');
                try {
                    const res = await fetch('/api/facts');
                    const facts = await res.json();
                    grid.innerHTML = facts.map(f => `
                        <div style="background:var(--panel-bg); border:1px solid var(--border-neon); border-radius:10px; padding:14px;">
                            <div style="font-size:13px;">${f.fact}</div>
                            <button style="margin-top:10px; background:#ef444420; color:#ef4444; border:1px solid #ef444440; padding:4px 8px; border-radius:6px; cursor:pointer;" onclick="deleteFact('${f.id}')">Elimina</button>
                        </div>
                    `).join('');
                } catch(e) {}
            }

            async function deleteFact(id) {
                await fetch(`/api/facts/${id}`, { method: 'DELETE' });
                loadVaultData();
                loadBrainSummary();
            }

            async function drawNexusGraph() {
                const canvas = document.getElementById('graph-canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = canvas.parentElement.clientWidth;
                canvas.height = canvas.parentElement.clientHeight - 60;
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                ctx.fillStyle = '#00f0ff';
                ctx.beginPath(); ctx.arc(canvas.width/2, canvas.height/2, 20, 0, Math.PI*2); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.fillText('Marco', canvas.width/2 - 18, canvas.height/2 + 35);
            }

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const text = input.value.trim();
                if(!text) return;

                appendMessage(text, 'user');
                input.value = '';

                const typingDiv = document.createElement('div');
                typingDiv.className = 'typing';
                typingDiv.innerText = '> PETER_OS ANALOG_PROCESSING...';
                container.appendChild(typingDiv);
                container.scrollTop = container.scrollHeight;

                try {
                    const res = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: text })
                    });
                    const data = await res.json();
                    container.removeChild(typingDiv);
                    if(data.reply) {
                        appendMessage(data.reply, 'peter', data.query_used, data.media);
                        setTimeout(loadBrainSummary, 1500);
                    }
                } catch(err) {
                    container.removeChild(typingDiv);
                    appendMessage('Errore di connessione al server.', 'peter');
                }
            });

            function appendMessage(text, sender, toolUsed = null, media = null) {
                const div = document.createElement('div');
                div.className = `msg ${sender}`;
                let html = '';
                if(toolUsed) {
                    html += `<div class="tool-badge">⚡ SYSTEM_EXEC: ${toolUsed}</div><br>`;
                }
                html += text;

                if(media && media.embed_url) {
                    html += `<div class="media-box"><iframe src="${media.embed_url}" allow="autoplay; encrypted-media" allowfullscreen></iframe></div>`;
                    document.getElementById('active-media-preview').innerHTML = `<strong style="color:var(--accent-cyan);">${media.title}</strong> in riproduzione.`;
                }

                div.innerHTML = html;
                container.appendChild(div);
                container.scrollTop = container.scrollHeight;
            }

            async function registerTelegramWebhook() {
                const token = document.getElementById('telegram-token-input').value.trim();
                if(!token) return alert('Inserisci un Token Telegram valido');
                const webhookUrl = `https://api.telegram.org/bot${token}/setWebhook?url=https://peter-backend-vgnb.onrender.com/telegram/webhook`;
                window.open(webhookUrl, '_blank');
            }

            loadBrainSummary();
        </script>
    </body>
    </html>
    """
