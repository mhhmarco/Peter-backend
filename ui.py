def get_dashboard_html() -> str:
    return """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Peter OS - Agent Dashboard</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            body { background: #09090b; color: #f4f4f5; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
            
            /* Top Navigation Header */
            header { height: 56px; border-bottom: 1px solid #27272a; padding: 0 20px; display: flex; align-items: center; justify-content: space-between; background: #09090b; }
            .logo-group { display: flex; align-items: center; gap: 10px; }
            .logo-badge { background: #2563eb; color: white; font-weight: 700; padding: 4px 10px; border-radius: 6px; font-size: 13px; letter-spacing: 0.5px; }
            header h1 { font-size: 15px; font-weight: 600; color: #fafafa; }
            
            /* Navigation Tabs */
            .nav-tabs { display: flex; gap: 6px; background: #141417; padding: 4px; border-radius: 10px; border: 1px solid #27272a; }
            .tab-btn { background: transparent; border: none; color: #a1a1aa; padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s; }
            .tab-btn.active { background: #2563eb; color: white; }
            .tab-btn:hover:not(.active) { color: #f4f4f5; background: #27272a; }

            .status-pill { display: flex; align-items: center; gap: 6px; background: #18181b; padding: 4px 10px; border-radius: 12px; border: 1px solid #27272a; font-size: 12px; color: #10b981; }
            .dot { width: 7px; height: 7px; background: #10b981; border-radius: 50%; }

            /* Main Content Container */
            .main-container { flex: 1; height: calc(100vh - 56px); overflow: hidden; position: relative; }
            .tab-content { display: none; height: 100%; width: 100%; }
            .tab-content.active { display: flex; }

            /* Tab 1: Chat Studio */
            .chat-grid { display: grid; grid-template-columns: 1fr 340px; width: 100%; height: 100%; }
            @media (max-width: 850px) { .chat-grid { grid-template-columns: 1fr; } .chat-sidebar { display: none; } }
            
            .chat-main { display: flex; flex-direction: column; height: 100%; background: #0c0c0e; border-right: 1px solid #27272a; }
            #chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
            .msg { max-width: 85%; padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.5; word-wrap: break-word; }
            .msg.user { align-self: flex-end; background: #2563eb; color: #fff; border-bottom-right-radius: 4px; }
            .msg.peter { align-self: flex-start; background: #18181b; color: #e4e4e7; border: 1px solid #27272a; border-bottom-left-radius: 4px; }
            .search-tag { font-size: 11px; background: #1e293b; color: #38bdf8; border: 1px solid #0284c7; padding: 3px 8px; border-radius: 6px; margin-bottom: 6px; display: inline-block; }
            .typing { font-style: italic; color: #71717a; font-size: 12px; }

            .chat-footer { padding: 14px 20px; border-top: 1px solid #1f1f23; background: #09090b; }
            form { display: flex; gap: 10px; }
            input { flex: 1; padding: 12px 18px; background: #18181b; border: 1px solid #27272a; border-radius: 24px; color: #fff; font-size: 14px; outline: none; }
            input:focus { border-color: #3b82f6; }
            button.send-btn { padding: 12px 22px; background: #2563eb; color: white; border: none; border-radius: 24px; font-weight: 600; cursor: pointer; }

            .chat-sidebar { padding: 18px; background: #09090b; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; }
            .card { background: #18181b; border: 1px solid #27272a; border-radius: 12px; padding: 16px; }
            .card-title { font-size: 12px; font-weight: 700; text-transform: uppercase; color: #a1a1aa; margin-bottom: 12px; display: flex; justify-content: space-between; }
            .fact-item { font-size: 13px; color: #d4d4d8; padding: 8px 0; border-bottom: 1px solid #27272a; line-height: 1.4; }
            .fact-item:last-child { border: none; }

            /* Tab 2: Memoria Vault */
            .vault-container { padding: 24px; width: 100%; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; }
            .vault-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #27272a; padding-bottom: 14px; }
            .vault-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 14px; }
            .vault-card { background: #18181b; border: 1px solid #27272a; border-radius: 12px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; gap: 12px; }
            .vault-text { font-size: 14px; color: #e4e4e7; line-height: 1.5; }
            .vault-meta { font-size: 11px; color: #71717a; display: flex; justify-content: space-between; align-items: center; }
            .del-btn { background: #ef444420; color: #ef4444; border: 1px solid #ef444440; padding: 4px 8px; border-radius: 6px; font-size: 11px; cursor: pointer; }

            /* Tab 3: Diario & Grafo */
            .placeholder-screen { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #71717a; gap: 12px; padding: 40px; text-align: center; }
        </style>
    </head>
    <body>
        <header>
            <div class="logo-group">
                <span class="logo-badge">PETER OS</span>
                <h1>Dashboard Agente</h1>
            </div>
            
            <div class="nav-tabs">
                <button class="tab-btn active" onclick="switchTab('chat')">💬 Chat Studio</button>
                <button class="tab-btn" onclick="switchTab('vault')">🧠 Memoria & Fatti</button>
                <button class="tab-btn" onclick="switchTab('diaries')">📖 Diario</button>
                <button class="tab-btn" onclick="switchTab('graph')">🕸️ Grafo Nexus</button>
            </div>

            <div class="status-pill"><div class="dot"></div> Agent Online</div>
        </header>

        <div class="main-container">
            <!-- TAB 1: CHAT STUDIO -->
            <div id="tab-chat" class="tab-content active">
                <div class="chat-grid">
                    <section class="chat-main">
                        <div id="chat-container">
                            <div class="msg peter">Ehi Marco, sono pronto. Ho integrato la ricerca web autonoma a doppio stadio: ora cerco su internet in modo intelligente se la tua richiesta lo richiede.</div>
                        </div>
                        <div class="chat-footer">
                            <form id="chat-form">
                                <input type="text" id="user-input" placeholder="Scrivi a Peter o chiedi informazioni..." autocomplete="off" required />
                                <button type="submit" class="send-btn">Invia</button>
                            </form>
                        </div>
                    </section>

                    <aside class="chat-sidebar">
                        <div class="card">
                            <div class="card-title">Memoria a Lungo Termine <span id="fact-count">0</span></div>
                            <div id="facts-summary">Caricamento memoria...</div>
                        </div>
                    </aside>
                </div>
            </div>

            <!-- TAB 2: MEMORIA VAULT -->
            <div id="tab-vault" class="tab-content">
                <div class="vault-container">
                    <div class="vault-header">
                        <h2>Archivio Memoria Concettuale (`user_facts`)</h2>
                        <span style="font-size: 13px; color: #a1a1aa;">Tutti i dati permanenti estratti dalle conversazioni</span>
                    </div>
                    <div id="vault-grid" class="vault-grid">
                        <div style="color: #71717a;">Caricamento in corso...</div>
                    </div>
                </div>
            </div>

            <!-- TAB 3: DIARIO SERALE -->
            <div id="tab-diaries" class="tab-content">
                <div class="placeholder-screen">
                    <div style="font-size: 32px;">📖</div>
                    <h3>Diario di Bordo Autonomo</h3>
                    <p>Le sintesi serali e la sentiment analysis giornaliera verranno salvate qui.</p>
                </div>
            </div>

            <!-- TAB 4: GRAFO NEXUS -->
            <div id="tab-graph" class="tab-content">
                <div class="placeholder-screen">
                    <div style="font-size: 32px;">🕸️</div>
                    <h3>Grafo Concettuale delle Entità</h3>
                    <p>Mappa dinamica dei nodi e delle relazioni tra persone, luoghi e progetti.</p>
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
                    if(facts.length > 0) {
                        grid.innerHTML = facts.map(f => `
                            <div class="vault-card">
                                <div class="vault-text">${f.fact}</div>
                                <div class="vault-meta">
                                    <span>${new Date(f.created_at).toLocaleDateString()}</span>
                                    <button class="del-btn" onclick="deleteFact('${f.id}')">Elimina</button>
                                </div>
                            </div>
                        `).join('');
                    } else {
                        grid.innerHTML = '<div style="color: #71717a;">Nessun fatto registrato in memoria.</div>';
                    }
                } catch(e) {
                    grid.innerHTML = '<div style="color: #ef4444;">Errore nel caricamento dei dati.</div>';
                }
            }

            async function deleteFact(id) {
                if(!confirm('Vuoi rimuovere questo fatto dalla memoria di Peter?')) return;
                try {
                    await fetch(`/api/facts/${id}`, { method: 'DELETE' });
                    loadVaultData();
                    loadBrainSummary();
                } catch(e) { alert('Errore eliminazione'); }
            }

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const text = input.value.trim();
                if(!text) return;

                appendMessage(text, 'user');
                input.value = '';

                const typingDiv = document.createElement('div');
                typingDiv.className = 'typing';
                typingDiv.innerText = 'Peter riflette ed elabora...';
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
                        appendMessage(data.reply, 'peter', data.searched_query);
                        setTimeout(loadBrainSummary, 1500);
                    }
                } catch(err) {
                    container.removeChild(typingDiv);
                    appendMessage('Errore di connessione al server.', 'peter');
                }
            });

            function appendMessage(text, sender, searchQuery = null) {
                const div = document.createElement('div');
                div.className = `msg ${sender}`;
                let html = '';
                if(searchQuery) {
                    html += `<div class="search-tag">🔍 Ricerca Web: ${searchQuery}</div><br>`;
                }
                html += text;
                div.innerHTML = html;
                container.appendChild(div);
                container.scrollTop = container.scrollHeight;
            }

            loadBrainSummary();
        </script>
    </body>
    </html>
    """
