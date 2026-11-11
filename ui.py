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

            .hud-grid { display: grid; grid-template-columns: 1fr 340px; width: 100%; height: 100%; }
            @media (max-width: 900px) { .hud-grid { grid-template-columns: 1fr; } .hud-sidebar { display: none; } }

            .hud-main { display: flex; flex-direction: column; height: 100%; border-right: 1px solid var(--border-neon); background: #070a10; }
            
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
            input, select, textarea { padding: 8px 12px; background: rgba(15, 23, 42, 0.9); border: 1px solid var(--border-neon); border-radius: 8px; color: #fff; font-size: 12px; outline: none; }
            input:focus, select:focus, textarea:focus { border-color: var(--accent-cyan); }
            button.send-btn { padding: 8px 16px; background: var(--accent-cyan); color: #000; border: none; border-radius: 8px; font-weight: 700; font-size: 12px; cursor: pointer; }

            .hud-sidebar { padding: 16px; background: var(--bg-core); display: flex; flex-direction: column; gap: 14px; overflow-y: auto; }
            .card { background: var(--panel-bg); border: 1px solid var(--border-neon); border-radius: 10px; padding: 14px; }
            .card-title { font-size: 10px; font-weight: 700; text-transform: uppercase; color: var(--accent-cyan); margin-bottom: 8px; display: flex; justify-content: space-between; }
            .fact-item { font-size: 11px; color: var(--text-main); padding: 6px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }

            /* LAYOUT NEXUS 3D */
            .nexus-container { display: grid; grid-template-columns: 1fr 360px; width: 100%; height: 100%; }
            .nexus-sidebar { background: var(--bg-core); border-left: 1px solid var(--border-neon); padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; }
            .nexus-badge { font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; }
            .badge-famiglia { background: #ef444430; color: #ef4444; border: 1px solid #ef4444; }
            .badge-amicizia { background: #3b82f630; color: #3b82f6; border: 1px solid #3b82f6; }
            .badge-lavoro { background: #10b98130; color: #10b981; border: 1px solid #10b981; }
            .badge-progetto { background: #f59e0b30; color: #f59e0b; border: 1px solid #f59e0b; }
            .badge-self { background: #00f0ff30; color: #00f0ff; border: 1px solid #00f0ff; }

            .relation-item { font-size: 11px; padding: 6px; background: rgba(255,255,255,0.03); border: 1px solid var(--border-neon); border-radius: 6px; margin-top: 4px; display: flex; justify-content: space-between; align-items: center; }

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

            <!-- TAB 3: GRAPH (NEXUS 3D) -->
            <div id="tab-graph" class="tab-content">
                <div class="nexus-container">
                    <div style="position: relative; height: 100%;">
                        <canvas id="graph-canvas" style="width: 100%; height: 100%; background: var(--panel-bg);"></canvas>
                        <div style="position: absolute; top: 12px; left: 12px; font-size: 11px; color: var(--text-dim); background: rgba(0,0,0,0.6); padding: 4px 8px; border-radius: 4px; border: 1px solid var(--border-neon);">
                            💡 Clicca su un nodo nel grafo per aprire la Scheda Persona.
                        </div>
                    </div>

                    <aside class="nexus-sidebar">
                        <!-- SCHEDA PERSONA SELEZIONATA -->
                        <div class="card">
                            <div class="card-title">SCHEDA ENTITÀ / PERSONA</div>
                            <div id="node-details">
                                <p style="font-size: 11px; color: var(--text-dim);">Seleziona una persona dal grafo a sinistra.</p>
                            </div>
                        </div>

                        <!-- FORMS INSERIMENTO DATI PREGRESSI -->
                        <div class="card">
                            <div class="card-title">INSERISCI DATI PREGRESSI NEXUS</div>
                            <form id="add-node-form" style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px;">
                                <input type="text" id="node-name" placeholder="Nome Persona / Entità" required />
                                <select id="node-category">
                                    <option value="Amicizia">Amicizia</option>
                                    <option value="Famiglia">Famiglia</option>
                                    <option value="Lavoro">Lavoro</option>
                                    <option value="Progetto">Progetto</option>
                                    <option value="Self">Self</option>
                                </select>
                                <textarea id="node-notes" placeholder="Note / Dettagli sul contatto..." rows="2"></textarea>
                                <button type="submit" class="send-btn">SALVA ENTITÀ</button>
                            </form>

                            <hr style="border-color: var(--border-neon); margin: 10px 0;">

                            <div class="card-title">AGGIUNGI COLLEGAMENTO TIPIZZATO</div>
                            <form id="add-edge-form" style="display: flex; flex-direction: column; gap: 8px;">
                                <select id="edge-source" required><option value="">Seleziona Origine...</option></select>
                                <select id="edge-target" required><option value="">Seleziona Destinazione...</option></select>
                                <input type="text" id="edge-label" placeholder="Tipo Legame (es. Fratello di, Collega di)" required />
                                <button type="submit" class="send-btn">CREA LEGAME</button>
                            </form>
                        </div>
                    </aside>
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
            let currentGraphData = { nodes: [], edges: [] };
            let renderedNodes = [];

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
                if (!canvas) return;
                const ctx = canvas.getContext('2d');
                canvas.width = canvas.parentElement.clientWidth;
                canvas.height = canvas.parentElement.clientHeight;
                
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                try {
                    const res = await fetch('/api/graph');
                    currentGraphData = await res.json();
                    const nodes = currentGraphData.nodes || [];
                    const edges = currentGraphData.edges || [];

                    updateSelectDropdowns(nodes);

                    const centerX = canvas.width / 2;
                    const centerY = canvas.height / 2;

                    const marcoNode = { id: 'marco-core', name: 'Marco', category: 'Self', x: centerX, y: centerY, r: 18 };
                    renderedNodes = [marcoNode];

                    ctx.fillStyle = '#00f0ff';
                    ctx.shadowBlur = 14;
                    ctx.shadowColor = '#00f0ff';
                    ctx.beginPath();
                    ctx.arc(centerX, centerY, marcoNode.r, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.shadowBlur = 0;

                    ctx.fillStyle = '#ffffff';
                    ctx.font = 'bold 12px sans-serif';
                    ctx.fillText('Marco', centerX - 18, centerY + 34);

                    if (nodes.length === 0) return;

                    const radius = Math.min(centerX, centerY) * 0.65;
                    const angleStep = (Math.PI * 2) / nodes.length;
                    const positions = { 'marco-core': { x: centerX, y: centerY } };

                    nodes.forEach((node, idx) => {
                        const angle = idx * angleStep;
                        const x = centerX + radius * Math.cos(angle);
                        const y = centerY + radius * Math.sin(angle);
                        positions[node.id] = { x, y };

                        renderedNodes.push({ ...node, x, y, r: 12 });

                        ctx.strokeStyle = 'rgba(0, 240, 255, 0.15)';
                        ctx.beginPath();
                        ctx.moveTo(centerX, centerY);
                        ctx.lineTo(x, y);
                        ctx.stroke();

                        let color = '#2563eb';
                        if (node.category === 'Famiglia') color = '#ef4444';
                        if (node.category === 'Lavoro') color = '#10b981';
                        if (node.category === 'Progetto') color = '#f59e0b';

                        ctx.fillStyle = color;
                        ctx.beginPath();
                        ctx.arc(x, y, 10, 0, Math.PI * 2);
                        ctx.fill();

                        ctx.fillStyle = '#f0f6fc';
                        ctx.font = '11px sans-serif';
                        ctx.fillText(node.name || 'Entità', x - 18, y + 22);
                    });

                    edges.forEach(edge => {
                        const p1 = positions[edge.source_id] || positions['marco-core'];
                        const p2 = positions[edge.target_id] || positions['marco-core'];
                        if (p1 && p2) {
                            ctx.strokeStyle = 'rgba(0, 240, 255, 0.4)';
                            ctx.beginPath();
                            ctx.moveTo(p1.x, p1.y);
                            ctx.lineTo(p2.x, p2.y);
                            ctx.stroke();

                            const midX = (p1.x + p2.x) / 2;
                            const midY = (p1.y + p2.y) / 2;
                            ctx.fillStyle = '#00f0ff';
                            ctx.font = '9px monospace';
                            ctx.fillText(edge.relation_label || 'collegato', midX - 15, midY - 4);
                        }
                    });

                } catch (e) {
                    console.error("Errore caricamento Nexus Graph:", e);
                }
            }

            document.getElementById('graph-canvas').addEventListener('click', (e) => {
                const rect = e.target.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                const clickY = e.clientY - rect.top;

                const clicked = renderedNodes.find(n => {
                    const dx = clickX - n.x;
                    const dy = clickY - n.y;
                    return Math.sqrt(dx*dx + dy*dy) <= n.r + 4;
                });

                if (clicked) {
                    showNodeCard(clicked);
                }
            });

            function showNodeCard(node) {
                const detailsDiv = document.getElementById('node-details');
                const edges = currentGraphData.edges || [];
                const nodes = currentGraphData.nodes || [];

                const nodeEdges = edges.filter(e => e.source_id === node.id || e.target_id === node.id);
                let catBadge = `<span class="nexus-badge badge-${(node.category || 'amicizia').toLowerCase()}">${node.category || 'Amicizia'}</span>`;

                let html = `
                    <div style="display:flex; justify-space-between; align-items:center; margin-bottom:8px;">
                        <h3 style="font-size:15px; color:#fff;">${node.name}</h3>
                        ${catBadge}
                    </div>
                    <p style="font-size:11px; color:var(--text-dim); margin-bottom:10px;">${node.notes || 'Nessuna nota aggiuntiva registrata.'}</p>
                    
                    <div style="font-size:10px; font-weight:bold; color:var(--accent-cyan); text-transform:uppercase; margin-bottom:6px;">
                        COLLEGAMENTI (${nodeEdges.length})
                    </div>
                `;

                if (nodeEdges.length === 0) {
                    html += `<p style="font-size:11px; color:var(--text-dim);">Nessuna relazione registrata.</p>`;
                } else {
                    nodeEdges.forEach(edge => {
                        const otherId = edge.source_id === node.id ? edge.target_id : edge.source_id;
                        const otherNode = nodes.find(n => n.id === otherId) || { name: 'Marco' };
                        html += `
                            <div class="relation-item">
                                <span><strong>${edge.relation_label}</strong> ➔ ${otherNode.name}</span>
                                <button style="background:none; border:none; color:#ef4444; cursor:pointer; font-size:10px;" onclick="deleteEdge('${edge.id}')">✖</button>
                            </div>
                        `;
                    });
                }

                if (node.id !== 'marco-core') {
                    html += `
                        <button style="margin-top:14px; width:100%; background:#ef444420; color:#ef4444; border:1px solid #ef444440; padding:6px; border-radius:6px; cursor:pointer; font-size:11px; font-weight:bold;" onclick="deleteNode('${node.id}')">
                            ELIMINA PERSONA
                        </button>
                    `;
                }

                detailsDiv.innerHTML = html;
            }

            function updateSelectDropdowns(nodes) {
                const srcSelect = document.getElementById('edge-source');
                const tgtSelect = document.getElementById('edge-target');

                let options = `<option value="marco-core">Marco (Self)</option>`;
                nodes.forEach(n => {
                    options += `<option value="${n.id}">${n.name} (${n.category || 'Amicizia'})</option>`;
                });

                srcSelect.innerHTML = options;
                tgtSelect.innerHTML = options;
            }

            document.getElementById('add-node-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const name = document.getElementById('node-name').value.trim();
                const category = document.getElementById('node-category').value;
                const notes = document.getElementById('node-notes').value.trim();

                if (!name) return;
                await fetch('/api/graph/node', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, category, notes })
                });

                document.getElementById('node-name').value = '';
                document.getElementById('node-notes').value = '';
                drawNexusGraph();
            });

            document.getElementById('add-edge-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const source_id = document.getElementById('edge-source').value;
                const target_id = document.getElementById('edge-target').value;
                const relation_label = document.getElementById('edge-label').value.trim();

                if (!source_id || !target_id || !relation_label || source_id === target_id) return;

                await fetch('/api/graph/edge', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source_id, target_id, relation_label })
                });

                document.getElementById('edge-label').value = '';
                drawNexusGraph();
            });

            async function deleteNode(id) {
                if (confirm("Eliminare questa persona e tutte le sue relazioni?")) {
                    await fetch(`/api/graph/node/${id}`, { method: 'DELETE' });
                    document.getElementById('node-details').innerHTML = '<p style="font-size:11px; color:var(--text-dim);">Persona eliminata.</p>';
                    drawNexusGraph();
                }
            }

            async function deleteEdge(id) {
                await fetch(`/api/graph/edge/${id}`, { method: 'DELETE' });
                drawNexusGraph();
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
