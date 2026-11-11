def get_dashboard_html() -> str:
    return """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Peter OS Dashboard</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
            body { background: #09090b; color: #f4f4f5; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
            header { height: 52px; border-bottom: 1px solid #27272a; padding: 0 16px; display: flex; align-items: center; justify-content: space-between; background: #09090b; }
            .logo { font-weight: 700; font-size: 14px; background: #2563eb; padding: 4px 10px; border-radius: 6px; color: white; }
            .status { font-size: 12px; color: #10b981; display: flex; align-items: center; gap: 6px; }
            .dot { width: 7px; height: 7px; background: #10b981; border-radius: 50%; }

            .dashboard-grid { flex: 1; display: grid; grid-template-columns: 1fr 340px; height: calc(100vh - 52px); overflow: hidden; }
            @media (max-width: 850px) { .dashboard-grid { grid-template-columns: 1fr; } .sidebar { display: none; } }

            .chat-section { display: flex; flex-direction: column; height: 100%; border-right: 1px solid #27272a; background: #0c0c0e; }
            #chat-container { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
            .msg { max-width: 85%; padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.45; word-wrap: break-word; }
            .msg.user { align-self: flex-end; background: #2563eb; color: #fff; border-bottom-right-radius: 4px; }
            .msg.peter { align-self: flex-start; background: #18181b; color: #e4e4e7; border: 1px solid #27272a; border-bottom-left-radius: 4px; }
            .typing { font-style: italic; color: #71717a; font-size: 12px; }

            .chat-footer { padding: 12px 16px; border-top: 1px solid #1f1f23; background: #09090b; }
            form { display: flex; gap: 8px; }
            input { flex: 1; padding: 12px 16px; background: #18181b; border: 1px solid #27272a; border-radius: 20px; color: #fff; font-size: 14px; outline: none; }
            button { padding: 12px 20px; background: #2563eb; color: white; border: none; border-radius: 20px; font-weight: 600; cursor: pointer; }

            .sidebar { padding: 16px; display: flex; flex-direction: column; gap: 16px; background: #09090b; overflow-y: auto; }
            .card { background: #18181b; border: 1px solid #27272a; border-radius: 12px; padding: 14px; }
            .card-title { font-size: 12px; font-weight: 700; text-transform: uppercase; color: #a1a1aa; margin-bottom: 10px; display: flex; justify-content: space-between; }
            .fact-item { font-size: 12px; color: #d4d4d8; padding: 6px 0; border-bottom: 1px solid #27272a; }
            .fact-item:last-child { border: none; }
        </style>
    </head>
    <body>
        <header>
            <div class="logo">PETER OS</div>
            <div class="status"><div class="dot"></div> Live Engine + Web Search</div>
        </header>

        <div class="dashboard-grid">
            <section class="chat-section">
                <div id="chat-container">
                    <div class="msg peter">Ehi Marco, Dashboard pronta e ricerca web attiva. Dimmi pure.</div>
                </div>
                <div class="chat-footer">
                    <form id="chat-form">
                        <input type="text" id="user-input" placeholder="Chiedi a Peter o cerca un posto..." autocomplete="off" required />
                        <button type="submit">Invia</button>
                    </form>
                </div>
            </section>

            <aside class="sidebar">
                <div class="card">
                    <div class="card-title">Memoria a Lungo Termine <span id="fact-count">0</span></div>
                    <div id="facts-container">Caricamento fatti...</div>
                </div>
                <div class="card">
                    <div class="card-title">Motore Ricerca Web</div>
                    <p style="font-size: 12px; color: #71717a;">DuckDuckGo Live Search integrato. Le informazioni sui locali e luoghi sono ora reali.</p>
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
                        factCount.innerText = data.long_term_facts.length;
                        factsContainer.innerHTML = data.long_term_facts.map(f => `
                            <div class="fact-item">🧠 ${f.fact}</div>
                        `).join('');
                    }
                } catch(e) {}
            }

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const text = input.value.trim();
                if(!text) return;

                appendMessage(text, 'user');
                input.value = '';

                const typingDiv = document.createElement('div');
                typingDiv.className = 'typing';
                typingDiv.innerText = 'Peter ricerca ed elabora...';
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
