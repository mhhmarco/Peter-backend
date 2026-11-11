def get_dashboard_html() -> str:
    return """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PETER OS - JARVIS HUD INTERACTIVE</title>
        <style>
            :root {
                --bg-core: #030712;
                --panel-bg: rgba(6, 15, 30, 0.85);
                --border-neon: rgba(0, 240, 255, 0.3);
                --accent-cyan: #00f0ff;
                --accent-orange: #ff5500;
                --accent-blue: #1d4ed8;
                --text-main: #f3f4f6;
                --text-dim: #9ca3af;
            }
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: "Segoe UI", -apple-system, sans-serif; }
            body { background: var(--bg-core); color: var(--text-main); height: 100vh; display: flex; flex-direction: column; overflow: hidden; background-image: radial-gradient(circle at 50% 50%, rgba(0, 240, 255, 0.05) 0%, transparent 80%); }

            header { height: 55px; border-bottom: 1px solid var(--border-neon); padding: 0 24px; display: flex; align-items: center; justify-content: space-between; background: rgba(3, 7, 18, 0.95); box-shadow: 0 0 15px rgba(0, 240, 255, 0.15); }
            .brand { display: flex; align-items: center; gap: 12px; }
            .arc-reactor { width: 16px; height: 16px; border: 2px solid var(--accent-cyan); border-radius: 50%; box-shadow: 0 0 12px var(--accent-cyan); animation: pulse 2s infinite; }
            @keyframes pulse { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.15); opacity: 0.7; } }
            .brand h1 { font-size: 15px; font-weight: 800; letter-spacing: 2px; color: #fff; text-shadow: 0 0 8px var(--accent-cyan); }

            .nav-tabs { display: flex; gap: 8px; background: rgba(15, 23, 42, 0.8); padding: 4px; border-radius: 12px; border: 1px solid var(--border-neon); }
            .tab-btn { background: transparent; border: none; color: var(--text-dim); padding: 6px 16px; border-radius: 8px; font-size: 11px; font-weight: 700; cursor: pointer; transition: all 0.2s; letter-spacing: 0.5px; }
            .tab-btn.active { background: linear-gradient(135deg, #1d4ed8, #00f0ff); color: #fff; box-shadow: 0 0 12px rgba(0, 240, 255, 0.4); }

            .main-container { flex: 1; height: calc(100vh - 55px); overflow: hidden; position: relative; }
            .tab-content { display: none; height: 100%; width: 100%; }
            .tab-content.active { display: flex; }

            /* JARVIS CHAT LAYOUT */
            .hud-grid { display: grid; grid-template-columns: 1fr 340px; width: 100%; height: 100%; }
            @media (max-width: 900px) { .hud-grid { grid-template-columns: 1fr; } .hud-sidebar { display: none; } }

            .hud-main { display: flex; flex-direction: column; height: 100%; border-right: 1px solid var(--border-neon); background: rgba(3, 7, 18, 0.6); }
            #chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; scroll-behavior: smooth; }
            
            .msg { max-width: 78%; padding: 12px 16px; border-radius: 14px; font-size: 13px; line-height: 1.5; word-wrap: break-word; }
            .msg.user { align-self: flex-end; background: linear-gradient(135deg, #1e3a8a, #2563eb); color: #fff; border: 1px solid rgba(0, 240, 255, 0.3); border-bottom-right-radius: 2px; }
            .msg.peter { align-self: flex-start; background: var(--panel-bg); color: var(--text-main); border: 1px solid var(--border-neon); border-bottom-left-radius: 2px; box-shadow: 0 0 10px rgba(0, 240, 255, 0.05); }

            .tool-badge { font-size: 10px; font-family: monospace; color: var(--accent-cyan); background: rgba(0, 240, 255, 0.1); border: 1px solid var(--border-neon); padding: 2px 6px; border-radius: 4px; margin-bottom: 6px; display: inline-block; }
            .media-box { margin-top: 8px; border-radius: 8px; overflow: hidden; border: 1px solid var(--border-neon); background: #000; width: 100%; max-width: 420px; }
            .media-box iframe { width: 100%; height: 210px; border: none; }
            .typing { font-style: italic; color: var(--accent-cyan); font-size: 11px; font-family: monospace; }

            /* OPEN MIC CONTROLS */
            .chat-footer { padding: 14px 20px; border-top: 1px solid var(--border-neon); background: rgba(3, 7, 18, 0.98); display: flex; gap: 10px; align-items: center; }
            form { display: flex; gap: 8px; flex: 1; }
            input, select, textarea { padding: 10px 16px; background: rgba(15, 23, 42, 0.9); border: 1px solid var(--border-neon); border-radius: 10px; color: #fff; font-size: 13px; outline: none; }
            input:focus, select:focus, textarea:focus { border-color: var(--accent-cyan); box-shadow: 0 0 8px rgba(0, 240, 255, 0.3); }
            button.send-btn { padding: 10px 20px; background: var(--accent-cyan); color: #000; border: none; border-radius: 10px; font-weight: 800; font-size: 11px; cursor: pointer; letter-spacing: 1px; }

            .mic-btn { padding: 10px 16px; background: rgba(255, 85, 0, 0.15); border: 1px solid var(--accent-orange); color: var(--accent-orange); border-radius: 10px; font-weight: 700; font-size: 11px; cursor: pointer; transition: all 0.2s; }
            .mic-btn.active { background: var(--accent-orange); color: #000; box-shadow: 0 0 15px var(--accent-orange); animation: pulse 1s infinite; }

            /* SIDEBAR TELEMETRIA IN CHAT */
            .hud-sidebar { padding: 16px; background: var(--bg-core); display: flex; flex-direction: column; gap: 14px; overflow-y: auto; }
            .card { background: var(--panel-bg); border: 1px solid var(--border-neon); border-radius: 12px; padding: 16px; }
            .card-title { font-size: 11px; font-weight: 800; text-transform: uppercase; color: var(--accent-cyan); margin-bottom: 10px; display: flex; justify-content: space-between; letter-spacing: 1px; }

            /* NEXUS 3D TAB LAYOUT */
            .nexus-container { display: grid; grid-template-columns: 1fr 380px; width: 100%; height: 100%; }
            .nexus-sidebar { background: var(--bg-core); border-left: 1px solid var(--border-neon); padding: 18px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; }
            .nexus-badge { font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; }
            .badge-famiglia { background: #ef444430; color: #ef4444; border: 1px solid #ef4444; }
            .badge-amicizia { background: #3b82f630; color: #3b82f6; border: 1px solid #3b82f6; }
            .badge-lavoro { background: #10b98130; color: #10b981; border: 1px solid #10b981; }

            /* TELEMETRY VIEW TAB */
            .telemetry-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; width: 100%; padding: 24px; overflow-y: auto; }
            .stat-box { background: var(--panel-bg); border: 1px solid var(--border-neon); border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 8px; }
            .stat-val { font-size: 28px; font-weight: 800; color: var(--accent-cyan); text-shadow: 0 0 10px var(--accent-cyan); }
            .stat-lbl { font-size: 11px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; }
        </style>
    </head>
    <body>
        <header>
            <div class="brand">
                <div class="arc-reactor"></div>
                <h1>PETER OS // JARVIS HUD</h1>
            </div>
            
            <div class="nav-tabs">
                <button class="tab-btn active" onclick="switchTab('chat')">⚡ CORE HUD</button>
                <button class="tab-btn" onclick="switchTab('graph')">🕸️ NEXUS CONTACTS</button>
                <button class="tab-btn" onclick="switchTab('telemetry')">📊 TELEMETRIA</button>
                <button class="tab-btn" onclick="switchTab('vault')">🧠 VAULT FACT</button>
                <button class="tab-btn" onclick="switchTab('settings')">⚙️ SETTINGS</button>
            </div>
        </header>

        <div class="main-container">
            <!-- TAB 1: CHAT STUDIO -->
            <div id="tab-chat" class="tab-content active">
                <div class="hud-grid">
                    <section class="hud-main">
                        <div id="chat-container">
                            <div class="msg peter">Sistemi JARVIS HUD attivi. Modalità Open-Mic disponibile. Di cosa ci occupiamo, Marco?</div>
                        </div>
                        <div class="chat-footer">
                            <button type="button" id="mic-toggle" class="mic-btn" onclick="toggleOpenMic()">🎙️ OPEN MIC: OFF</button>
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
                        <div class="card">
                            <div class="card-title">STATO TELEMETRIA</div>
                            <div style="font-size:11px; color:var(--accent-cyan); font-family:monospace;" id="telemetry-quick">SYSTEM: ONLINE</div>
                        </div>
                    </aside>
                </div>
            </div>

            <!-- TAB 2: NEXUS CONTACTS VAULT -->
            <div id="tab-graph" class="tab-content">
                <div class="nexus-container">
                    <div style="position: relative; height: 100%;">
                        <canvas id="graph-canvas" style="width: 100%; height: 100%; background: var(--panel-bg);"></canvas>
                        <div style="position: absolute; top: 12px; left: 12px; font-size: 11px; color: var(--text-dim); background: rgba(0,0,0,0.7); padding: 6px 12px; border-radius: 6px; border: 1px solid var(--border-neon);">
                            💡 Clicca su una Persona nel Grafo per aprire la Scheda Contatto.
                        </div>
                    </div>

                    <aside class="nexus-sidebar">
                        <div class="card">
                            <div class="card-title">SCHEDA CONTATTO COMPLETA</div>
                            <div id="node-details">
                                <p style="font-size: 11px; color: var(--text-dim);">Seleziona una persona dal grafo a sinistra.</p>
                            </div>
                        </div>

                        <div class="card">
                            <div class="card-title">INSERISCI CONTATTO PREGRESSO</div>
                            <form id="add-node-form" style="display: flex; flex-direction: column; gap: 8px;">
                                <input type="text" id="node-name" placeholder="Nome Persona" required />
                                <input type="text" id="node-role" placeholder="Ruolo / Professione" />
                                <input type="text" id="node-phone" placeholder="Telefono" />
                                <input type="email" id="node-email" placeholder="Email" />
                                <select id="node-category">
                                    <option value="Amicizia">Amicizia</option>
                                    <option value="Famiglia">Famiglia</option>
                                    <option value="Lavoro">Lavoro</option>
                                    <option value="Progetto">Progetto</option>
                                </select>
                                <textarea id="node-notes" placeholder="Note / Storia..." rows="2"></textarea>
                                <button type="submit" class="send-btn">SALVA IN RUBRICA</button>
                            </form>
                        </div>
                    </aside>
                </div>
            </div>

            <!-- TAB 3: TELEMETRIA E WORKFLOW LIVE -->
            <div id="tab-telemetry" class="tab-content">
                <div class="telemetry-grid">
                    <div class="stat-box">
                        <div class="stat-lbl">Stato Sistema Backend</div>
                        <div class="stat-val" id="tel-status">ONLINE</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-lbl">Uptime Server</div>
                        <div class="stat-val" id="tel-uptime">0s</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-lbl">Contatti in Rubrica Nexus</div>
                        <div class="stat-val" id="tel-nodes">0</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-lbl">Memorie Permanenti Vault</div>
                        <div class="stat-val" id="tel-facts">0</div>
                    </div>
                </div>
            </div>

            <!-- TAB 4: VAULT FACTS -->
            <div id="tab-vault" class="tab-content">
                <div style="padding: 20px; width: 100%; overflow-y: auto;">
                    <h2 style="margin-bottom: 14px; font-size: 16px;">Archivio Memoria Concettuale (`user_facts`)</h2>
                    <div id="vault-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px;"></div>
                </div>
            </div>

            <!-- TAB 5: SETTINGS -->
            <div id="tab-settings" class="tab-content">
                <div class="settings-container" style="padding: 24px; max-width: 700px; margin: 0 auto;">
                    <h2 style="font-size: 16px; margin-bottom: 16px;">Impostazioni Sistema & Telegram</h2>
                    <div class="card">
                        <h3 style="font-size: 14px; margin-bottom: 6px;">Telegram Bot Webhook</h3>
                        <p style="font-size: 11px; color: var(--text-dim); margin-bottom: 12px;">Registra l'URL per chattare con Peter via Telegram.</p>
                        <button class="send-btn" onclick="registerWebhook()">Registra Webhook</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let openMicActive = false;
            let recognition = null;

            // INIZIALIZZAZIONE OPEN-MIC VOCALE
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRecognition();
                recognition.lang = 'it-IT';
                recognition.continuous = false;
                recognition.interimResults = false;

                recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    document.getElementById('user-input').value = transcript;
                    submitChatMessage(transcript);
                };

                recognition.onend = () => {
                    if (openMicActive) {
                        recognition.start();
                    }
                };
            }

            function toggleOpenMic() {
                const btn = document.getElementById('mic-toggle');
                if (!recognition) {
                    alert('Riconoscimento vocale non supportato dal browser.');
                    return;
                }

                openMicActive = !openMicActive;
                if (openMicActive) {
                    btn.classList.add('active');
                    btn.innerText = '🎙️ OPEN MIC: ON (ASCOLTO...)';
                    recognition.start();
                } else {
                    btn.classList.remove('active');
                    btn.innerText = '🎙️ OPEN MIC: OFF';
                    recognition.stop();
                }
            }

            function speakText(text) {
                if ('speechSynthesis' in window) {
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.lang = 'it-IT';
                    window.speechSynthesis.speak(utterance);
                }
            }

            function switchTab(tabId) {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                event.target.classList.add('active');
                document.getElementById(`tab-${tabId}`).classList.add('active');

                if(tabId === 'vault') loadVaultData();
                if(tabId === 'graph') drawNexusGraph();
                if(tabId === 'telemetry') loadTelemetryData();
            }

            const form = document.getElementById('chat-form');
            const input = document.getElementById('user-input');
            const container = document.getElementById('chat-container');

            async function submitChatMessage(text) {
                appendMessage(text, 'user');
                input.value = '';

                const typingDiv = document.createElement('div');
                typingDiv.className = 'typing';
                typingDiv.innerText = '> JARVIS_PROCESSING...';
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
                        if (openMicActive) speakText(data.reply);
                    }
                } catch(err) {
                    container.removeChild(typingDiv);
                    appendMessage('Errore di connessione al server.', 'peter');
                }
            }

            form.addEventListener('submit', (e) => {
                e.preventDefault();
                const text = input.value.trim();
                if(text) submitChatMessage(text);
            });

            function appendMessage(text, sender, toolUsed = null, media = null) {
                const div = document.createElement('div');
                div.className = `msg ${sender}`;
                let html = '';
                if(toolUsed) html += `<div class="tool-badge">⚡ ${toolUsed}</div><br>`;
                html += text;
                if(media && media.embed_url) {
                    html += `<div class="media-box"><iframe src="${media.embed_url}" allow="autoplay; encrypted-media" allowfullscreen></iframe></div>`;
                }
                div.innerHTML = html;
                container.appendChild(div);
                container.scrollTop = container.scrollHeight;
            }

            async function loadTelemetryData() {
                try {
                    const res = await fetch('/api/telemetry');
                    const data = await res.json();
                    document.getElementById('tel-status').innerText = data.status;
                    document.getElementById('tel-uptime').innerText = data.uptime_seconds + 's';
                    document.getElementById('tel-nodes').innerText = data.stats.nexus_nodes;
                    document.getElementById('tel-facts').innerText = data.stats.long_term_facts;
                } catch(e) {}
            }

            // NEXUS GRAPH RENDERING & CONTACT CARD HANDLER
            async function drawNexusGraph() {
                const canvas = document.getElementById('graph-canvas');
                if (!canvas) return;
                const ctx = canvas.getContext('2d');
                canvas.width = canvas.parentElement.clientWidth;
                canvas.height = canvas.parentElement.clientHeight;
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                try {
                    const res = await fetch('/api/graph');
                    const data = await res.json();
                    const nodes = data.nodes || [];
                    const centerX = canvas.width / 2;
                    const centerY = canvas.height / 2;

                    ctx.fillStyle = '#00f0ff';
                    ctx.shadowBlur = 15;
                    ctx.shadowColor = '#00f0ff';
                    ctx.beginPath(); ctx.arc(centerX, centerY, 16, 0, Math.PI * 2); ctx.fill();
                    ctx.shadowBlur = 0;

                    ctx.fillStyle = '#ffffff'; ctx.font = 'bold 12px sans-serif'; ctx.fillText('Marco', centerX - 18, centerY + 32);

                    const radius = Math.min(centerX, centerY) * 0.65;
                    const angleStep = (Math.PI * 2) / (nodes.length || 1);

                    nodes.forEach((node, idx) => {
                        const angle = idx * angleStep;
                        const x = centerX + radius * Math.cos(angle);
                        const y = centerY + radius * Math.sin(angle);

                        ctx.strokeStyle = 'rgba(0, 240, 255, 0.2)';
                        ctx.beginPath(); ctx.moveTo(centerX, centerY); ctx.lineTo(x, y); ctx.stroke();

                        ctx.fillStyle = '#2563eb';
                        ctx.beginPath(); ctx.arc(x, y, 10, 0, Math.PI * 2); ctx.fill();

                        ctx.fillStyle = '#f0f6fc'; ctx.font = '11px sans-serif';
                        ctx.fillText(node.name, x - 18, y + 22);
                    });
                } catch(e) {}
            }

            document.getElementById('add-node-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const name = document.getElementById('node-name').value.trim();
                const role = document.getElementById('node-role').value.trim();
                const phone = document.getElementById('node-phone').value.trim();
                const email = document.getElementById('node-email').value.trim();
                const category = document.getElementById('node-category').value;
                const notes = document.getElementById('node-notes').value.trim();

                await fetch('/api/graph/node', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, role, phone, email, category, notes })
                });

                document.getElementById('add-node-form').reset();
                drawNexusGraph();
            });

            function registerWebhook() {
                const token = prompt("Inserisci il tuo Token Telegram da @BotFather:");
                if(token) window.open(`https://api.telegram.org/bot${token}/setWebhook?url=https://peter-backend-vgnb.onrender.com/telegram/webhook`, '_blank');
            }
        </script>
    </body>
    </html>
    """
