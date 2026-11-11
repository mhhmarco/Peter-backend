// Da integrare nello script JS dentro ui.py

async function drawNexusGraph() {
    const canvas = document.getElementById('graph-canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight - 40;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    try {
        const res = await fetch('/api/graph');
        const data = await res.json();
        const nodes = data.nodes || [];
        const edges = data.edges || [];

        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;

        // Disegna nodo centrale (Marco)
        ctx.fillStyle = '#00f0ff';
        ctx.shadowBlur = 15;
        ctx.shadowColor = '#00f0ff';
        ctx.beginPath();
        ctx.arc(centerX, centerY, 18, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 12px sans-serif';
        ctx.fillText('Marco (Self)', centerX - 35, centerY + 34);

        if (nodes.length === 0) {
            ctx.fillStyle = '#8b949e';
            ctx.font = '12px sans-serif';
            ctx.fillText('Nessun nodo registrato nel database.', 20, 30);
            return;
        }

        // Calcola posizioni orbitali per i nodi del DB
        const radius = Math.min(centerX, centerY) * 0.65;
        const angleStep = (Math.PI * 2) / nodes.length;

        const nodePositions = {};

        nodes.forEach((node, index) => {
            const angle = index * angleStep;
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);
            nodePositions[node.id] = { x, y, name: node.name || node.title || 'Nodo' };

            // Linea verso il centro
            ctx.strokeStyle = 'rgba(0, 240, 255, 0.2)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.lineTo(x, y);
            ctx.stroke();

            // Disegna nodo satellitare
            ctx.fillStyle = '#2563eb';
            ctx.beginPath();
            ctx.arc(x, y, 10, 0, Math.PI * 2);
            ctx.fill();

            // Etichetta nodo
            ctx.fillStyle = '#f0f6fc';
            ctx.font = '11px sans-serif';
            ctx.fillText(nodePositions[node.id].name, x - 20, y + 22);
        });

        // Disegna collegamenti (edges) tra i nodi
        edges.forEach(edge => {
            const source = nodePositions[edge.source_id];
            const target = nodePositions[edge.target_id];
            if (source && target) {
                ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
                ctx.beginPath();
                ctx.moveTo(source.x, source.y);
                ctx.lineTo(target.x, target.y);
                ctx.stroke();
            }
        });

    } catch (e) {
        console.error("Errore nel caricamento del grafo:", e);
    }
}
