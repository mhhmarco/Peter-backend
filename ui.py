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
                --panel-bg: rgba(10, 16, 26, 0.85);
                --border-neon: rgba(0, 240, 255, 0.2);
                --accent-cyan: #00f0ff;
                --accent-blue: #2563eb;
                --text-main: #f0f6fc;
                --text-dim: #8b949e;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            body { background: var(--bg-core); color: var(--text-main); height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
            
            header { height: 50px; border-bottom: 1px solid var(--border-neon); padding: 0 20px; display: flex; align-items: center; justify-content: space-between; background: rgba(4, 7, 12, 0.95); }
            .brand { display: flex; align-items: center; gap: 10px; }
            .brand-glow { width: 10px; height: 10px; background: var(--accent-cyan); border-radius: 50%; box-shadow: 0 0 10px var(--accent-cyan); }
            .brand h1 { font-size: 14px; font-weight: 700; letter-spacing: 1px; color: #fff; }
            
            .nav-tabs { display: flex; gap: 6px; background: rgba(15, 23, 42, 0.8); padding: 3px; border-radius: 10px; border: 1px solid var(--border-neon); }
            .tab-btn { background: transparent; border: none; color: var(--text-dim); padding: 6px 14px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
            .tab-btn.active { background: var(--accent-blue); color: #fff; box-shadow: 0 0 8px rgba(37, 99, 235, 0.5); }

            .main-container { flex: 1; height: calc(100vh - 50px); overflow: hidden; position: relative; }
            .tab-content { display: none; height: 100%; width: 100%; }
            .tab-content.active { display: flex; }

            /* HUD Layout Compatto con Chat ridotta */
            .hud-grid { display: grid; grid-template-columns: 1fr 340px; width: 100%; height: 100%; }
            @media (max-width: 900px) { .hud-grid { grid-template-columns: 1fr; } .hud-sidebar { display: none; } }

            .hud-main { display: flex; flex-direction: column; height: 100%; border-right: 1px solid var(--border-neon); background: #070a10; }
            
            /* Chat Container scrollabile fluidamente */
            #chat-container { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; scroll-behavior: smooth; }
            
            .msg { max-width: 80%; padding: 10px 14px; border-radius: 14px; font-size: 13px; line-height: 1.45; word-wrap: break-word; }
            .msg.user { align-self: flex-end; background: linear-gradient(135deg, #1e40af, #2563eb); color: #fff; border-bottom-right-radius: 3px; }
            .msg.peter { align-self: flex-start; background: var(--panel-bg); color: var(--text-main); border: 1px solid var(--border-neon); border-bottom-left-radius: 3px; }
            
            .tool-badge { font-size: 10px; font-family: monospace; color: var(--accent-cyan); background: rgba(0, 240, 255, 0.1); border: 1px solid var(--border-neon); padding: 2px 6px; border-radius: 4px; margin-bottom: 6px; display: inline-block; }
            .media-box { margin-top: 8px; border-radius: 8px; overflow: hidden; border: 1px solid var(--border-neon); background: #000; width: 100%; max-width: 420px; }
            .media-box iframe { width: 100%; height: 200px; border: none; }
            .typing { font-style: italic; color: var(--accent-cyan); font-size: 11px; font-family: monospace; }

            .chat-footer { padding: 12px 16px; border-top: 1px solid var(--border-neon); background: rgba(4, 7, 12, 0.98); }
            form { display: flex; gap: 8px; }
            input { flex: 1; padding: 10px 16px; background: rgba(15, 23, 42, 0.9); border: 1px solid var(--border-neon); border-radius: 20px; color: #fff; font-size: 13px; outline: none; }
            input:focus { border-color: var(--accent-cyan); }
            button.send-btn { padding: 10px 20px; background: var(--accent-cyan); color: #000; border: none; border-radius: 20px; font-weight: 700; font-size: 12px; cursor: pointer; }

            /* Sidebar Compatta */
            .hud-sidebar { padding: 16px; background: var(--bg-core); display: flex; flex-direction: column; gap: 14px; overflow-y: auto; }
            .card { background: var(--panel-bg); border: 1px solid var(--border-neon); border-radius: 10px; padding: 14px; }
            .card-title { font-size: 10px; font-weight: 700; text-transform: uppercase; color: var(--accent-cyan); margin-bottom: 8px; display: flex; justify-content: space-between; }
            .fact-item { font-size: 11px; color: var(--text-main); padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }

            .settings-container { padding: 24px; max-width: 700px; margin: 0 auto; width: 100%; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; }
            .setting-row { background: var(--panel-bg); border: 1px solid var(--border-neon); border-radius: 10px; padding: 16px; display: flex; justify-content: space-between; align-items: center; }
        </style>
    </head>
    <body>
        <header>
            <div class="brand">
                <div class="brand-glow"></div>
                <h1>PETER OS</h1>
            </div>
            
            <div class="nav-tabs">
                <button class="tab-btn active" onclick="switchTab('chat')">⚡ JARVIS Core</button>
                <button class="tab-btn" onclick="switchTab('vault')">🧠 Cervello & Memoria</button>
                <button class="tab-btn" onclick="switchTab('graph')">🕸️ Nexus 3D</button>
                <button class="tab-btn" onclick="switchTab('settings')">⚙️ Impostazioni</button>
            </div>
        </header>

        <div class="main-container">
            <!-- TAB 1: CHAT STUDIO -->
            <div id="tab-chat" class="tab-content active">
                <div class="hud-grid">
                    <section class="hud-main">
                        <div id="chat-container">
                            <div class="msg peter">Sistemi operativi attivi con architettura a 3 modelli. Di cosa ci occupiamo?</div>
                        </div>
                        <div class="chat-footer">
                            <form id="chat-form">
                                <input type="text" id="user-input" placeholder="Comanda a Peter o richiedi media..." autocomplete="off" required />
                                <button type="submit" class="send-btn">ESEGUI</button>
                            </form>
                        </div>
                    </section>

                    <aside class="hud-sidebar">
                        <div class="card">
                            <div class="card-title">MEMORIA ATTIVA <span id="fact-count">0</span></div>
                            <div id="facts-summary">Sincronizzazione dati...</div>
                        </div>
                    </aside>
                </div>
            </div>

            <!-- TAB 2: VAULT -->
            <div id="tab-vault" class="tab-content">
                <div style="padding: 20px; width: 100%; overflow-y: auto;">
                    <h2 style="margin-bottom: 14px; font-size: 16px;">Archivio Memoria Concettuale (`user_facts`)</h2>
                    <div id="vault-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px;"></div>
                </div>
            </div>

            <!-- TAB 3: GRAPH -->
            <div id="tab-graph" class="tab-content">
                <div style="width: 100%; height: 100%; padding: 16px; display: flex; flex-direction: column;">
                    <h2 style="margin-bottom: 10px; font-size: 16px;">Grafo Concettuale Entità (Nexus)</h2>
                    <canvas id="graph-canvas" style="flex: 1; background: var(--panel-bg); border: 1px solid var(--border-neon); border-radius: 10px;"></canvas>
                </div>
            </div>

            <!-- TAB 4: SETTINGS -->
            <div id="tab-settings" class="tab-content">
                <div class="settings-container">
                    <h2 style="font-size: 16px;">Impostazioni Sistema & Telegram</h2>
                    <div class="setting-row">
                        <div>
                            <h3 style="font-size: 14px;">Telegram Bot Webhook</h3>
                            <p style="font-size: 11px; color: var(--text-dim);">Registra l'URL del server per abilitare la chat da smartphone.</p>
                        </div>
                        <button class="send-btn" onclick="registerWebhook()">Registra Webhook</button>
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
                        <div style="background:var(--panel-bg); border:1px solid var(--border-neon); border-radius:8px; padding:12px;">
                            <div style="font-size:12px;">${f.fact}</div>
                            <button style="margin-top:8px; background:#ef444420; color:#ef4444; border:1px solid #ef444440; padding:3px 6px; border-radius:4px; cursor:pointer; font-size:10px;" onclick="deleteFact('${f.id}')">Elimina</button>
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
                canvas.height = canvas.parentElement.clientHeight - 40;
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                ctx.fillStyle = '#00f0ff';
                ctx.beginPath(); ctx.arc(canvas.width/2, canvas.height/2, 16, 0, Math.PI*2); ctx.fill();
                ctx.fillStyle = '#ffffff'; ctx.font = '12px sans-serif'; ctx.fillText('Marco', canvas.width/2 - 16, canvas.height/2 + 30);
            }

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const text = input.value.trim();
                if(!text) return;

                appendMessage(text, 'user');
                input.value = '';

                const typingDiv = document.createElement('div');
                typingDiv.className = 'typing';
                typingDiv.innerText = '> MULTI_MODEL_PROCESSING...';
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
                        setTimeout(loadBrainSummary, 1200);
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
                    html += `<div class="tool-badge">⚡ ${toolUsed}</div><br>`;
                }
                html += text;

                if(media && media.embed_url) {
                    html += `<div class="media-box"><iframe src="${media.embed_url}" allow="autoplay; encrypted-media" allowfullscreen></iframe></div>`;
                }

                div.innerHTML = html;
                container.appendChild(div);
                container.scrollTop = container.scrollHeight;
            }

            function registerWebhook() {
                const token = prompt("Inserisci il tuo Token Telegram da @BotFather:");
                if(token) {
                    window.open(`https://api.telegram.org/bot${token}/setWebhook?url=https://peter-backend-vgnb.onrender.com/telegram/webhook`, '_blank');
                }
            }

            loadBrainSummary();
        </script>
    </body>
    </html>
    """
