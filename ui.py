def get_dashboard_html() -> str:
    return """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Peter OS - Dashboard</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
            body { background-color: #09090b; color: #f4f4f5; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
            header { height: 56px; border-bottom: 1px solid #27272a; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; background: #09090b; }
            .logo-group { display: flex; align-items: center; gap: 12px; }
            .logo-badge { background: #3b82f6; color: white; font-weight: 700; padding: 4px 8px; border-radius: 6px; font-size: 12px; letter-spacing: 0.5px; }
            header h1 { font-size: 16px; font-weight: 600; color: #fafafa; }
            .system-status { display: flex; gap: 16px; align-items: center; font-size: 12px; color: #a1a1aa; }
            .status-pill { display: flex; align-items: center; gap: 6px; background: #18181b; padding: 4px 10px; border-radius: 12px; border: 1px solid #27272a; }
            .dot { width: 7px; height: 7px; background: #10b981; border-radius: 50%; }
            .dashboard-grid { flex: 1; display: grid; grid-template-columns: 1fr 380px; height: calc(100vh - 56px); overflow: hidden; }
            .chat-section { display: flex; flex-direction: column; height: 100%; border-right: 1px solid #27272a; background: #0c0c0e; }
            .section-header { padding: 14px 20px; border-bottom: 1px solid #1f1f23; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #71717a; display: flex; justify-content: space-between; }
            #chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
            .msg { max-width: 82%; padding: 12px 16px; border-radius: 14px; font-size: 14px; line-height: 1.5; word-wrap: break-word; }
            .msg.user { align-self: flex-end; background: #2563eb; color: #ffffff; border-bottom-right-radius: 3px; }
            .msg.peter { align-self: flex-start; background: #18181b; color: #e4e4e7; border: 1px solid #27272a; border-bottom-left-radius: 3px; }
            .typing { font-style: italic; color: #71717a; font-size: 12px; align-self: flex-start; }
            .chat-footer { padding: 16px 20px; border-top: 1px solid #1f1f23; background: #09090b; }
            form { display: flex; gap: 10px; }
            input { flex: 1; padding: 12px 16px; background: #18181b; border: 1px solid #27272a; border-radius: 20px; color: #ffffff; font-size: 14px; outline: none; }
            input:focus { border-color: #3b82f6; }
            button { padding: 12px 20px; background: #2563eb; color: white; border: none; border-radius: 20px; font-weight: 600; cursor: pointer; transition: background 0.2s; font-size: 14px; }
            button:hover { background: #1d4ed8; }
            .brain-sidebar { display: flex; flex-direction: column; height: 100%; background: #09090b; overflow-y: auto; }
            .widget-card { padding: 18px; border-bottom: 1px solid #27272a; }
            .widget-title { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #a1a1aa; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
            .facts-list { display: flex; flex-direction: column; gap: 8px; max-height: 240px; overflow-y: auto; }
            .fact-item { background: #18181b; border: 1px solid #27272a; padding: 10px 12px; border-radius: 8px; font-size: 13px; color: #d4d4d8; line-height: 1.4; display: flex; gap: 8px; align-items: flex-start; }
            .fact-icon { color: #3b82f6; font-weight: bold; }
            .nexus-box { background: #141417; border: 1px dashed #27272a; border-radius: 10px; height: 160px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 16px; color: #71717a; gap: 8px; }
            .nexus-box p { font-size: 12px; }
            .badge-active { background: #10b98120; color: #10b981; border: 1px solid #10b98140; font-size: 10px; padding: 2px 6px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <header>
            <div class="logo-group">
                <span class="logo-badge">PETER OS</span>
                <h1>Dashboard Agente</h1>
            </div>
            <div class="system-status">
                <div class="status-pill"><div class="dot"></div> Groq GPT-OSS 120B</div>
                <div class="status-pill"><div class="dot"></div> Supabase DB</div>
            </div>
        </header>

        <div class="dashboard-grid">
            <section class="chat-section">
                <div class="section-header">
                    <span>Interfaccia Dialogo</span>
                    <span>Live Session</span>
                </div>
                <div id="chat-container">
                    <div class="msg peter">Ehi Marco, Dashboard modulare pronta.</div>
                </div>
                <div class="chat-footer">
                    <form id="chat-form">
                        <input type="text" id="user-input" placeholder="Parla con Peter..." autocomplete="off" required />
                        <button type="submit">Invia</button>
                    </form>
                </div>
            </section>

            <aside class="brain-sidebar">
                <div class="widget-card">
                    <div class="widget-title">
                        <span>Memoria a Lungo Termine</span>
                        <span id="fact-count" class="badge-active">0 Fatti</span>
                    </div>
                    <div id="facts-container" class="facts-list">
                        <div class="fact-item"><span class="fact-icon">•</span> Caricamento memoria in corso...</div>
                    </div>
                </div>

                <div class="widget-card">
                    <div class="widget-title">
                        <span>Grafo Concettuale (Nexus)</span>
                        <span class="badge-active">Engine 2.0</span>
                    </div>
                    <div class="nexus-box">
                        <div style="font-size: 20px;">🕸️</div>
                        <strong style="color: #e4e4e7; font-size: 13px;">Mappa Nodi & Entità</strong>
                        <p>Integrazione diretta con il motore visuale in arrivo.</p>
                    </div>
                </div>
            </aside>
        </div>

        <script>
            const form = document.getElementById('chat-form');
            const input = document.getElementById('user-input');
            const container = document.getElementById('chat-container');
            const factsContainer = document.getElementById('facts-container');
            const factCount = document.getElementById('fact-count');

            async function loadBrainData() {
                try {
                    const res = await fetch('/memories');
                    const data = await res.json();
                    if(data.connected && data.long_term_facts) {
                        factCount.innerText = `${data.long_term_facts.length} Fatti`;
                        if(data.long_term_facts.length > 0) {
                            factsContainer.innerHTML = data.long_term_facts.map(f => `
                                <div class="fact-item">
                                    <span class="fact-icon">🧠</span>
                                    <span>${f.fact}</span>
                                </div>
                            `).join('');
                        } else {
                            factsContainer.innerHTML = '<div class="fact-item">Nessun fatto registrato.</div>';
                        }
                    }
                } catch(e) {
                    console.error("Errore caricamento memoria:", e);
                }
            }

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const text = input.value.trim();
                if(!text) return;

                appendMessage(text, 'user');
                input.value = '';

                const typingDiv = document.createElement('div');
                typingDiv.className = 'typing';
                typingDiv.innerText = 'Peter elabora...';
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
                        appendMessage(data.reply, 'peter');
                        setTimeout(loadBrainData, 1500);
                    }
                } catch(err) {
                    container.removeChild(typingDiv);
                    appendMessage('Errore di connessione al server.', 'peter');
                }
            });

            function appendMessage(text, sender) {
                const div = document.createElement('div');
                div.className = `msg ${sender}`;
                div.innerText = text;
                container.appendChild(div);
                container.scrollTop = container.scrollHeight;
            }

            loadBrainData();
        </script>
    </body>
    </html>
    """
