// SmallChip AI — chat-first chip placement co-pilot (v0.3.0)
//
// Architecture:
//   - User uploads a .def (or picks an example)
//   - User types a plain-English request
//   - Server runs V3 GAT (best-possible placer) and returns:
//       * reply text
//       * placed_def (the placed .def text)
//       * gds_base64 + gds_filename (OpenROAD-ready GDS)
//   - Frontend shows the reply, the .def link, and the .gds link
//
// The in-app 3D viz was removed in v0.3.0 — the user wanted the
// GDS delivered so they can use OpenROAD (or KLayout / gds-viewer.com)
// to view the 3D layout externally. The app stays chat-first and
// lightweight.

let currentFile = null;
let sessionId = null;
let lastResult = null;

const $ = (id) => document.getElementById(id);
const chatBody = $('chatBody');
const userInput = $('userInput');
const sendBtn = $('sendBtn');
const statusText = $('statusText');
const chatStatus = $('chatStatus');
const welcome = $('welcome');

// ===== File upload =====
const uploadZone = $('uploadZone');
const fileInput = $('fileInput');
const fileCard = $('fileCard');
const fileName = $('fileName');
const fileMeta = $('fileMeta');
const examples = $('examples');

uploadZone.addEventListener('click', () => fileInput.click());
uploadZone.addEventListener('dragover', e => { e.preventDefault(); uploadZone.classList.add('dragging'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragging'));
uploadZone.addEventListener('drop', e => {
    e.preventDefault();
    uploadZone.classList.remove('dragging');
    if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', e => {
    if (e.target.files[0]) setFile(e.target.files[0]);
});

function setFile(file) {
    if (!file.name.endsWith('.def')) {
        alert('Please upload a .def file');
        return;
    }
    currentFile = file;
    fileName.textContent = file.name;
    fileMeta.textContent = `${(file.size / 1024).toFixed(1)} KB · DEF format`;
    fileCard.classList.remove('hidden');
    statusText.textContent = 'Design loaded';
    chatStatus.classList.add('online');
    enableInput();
}

examples.addEventListener('click', async e => {
    if (!e.target.dataset.file) return;
    const filename = e.target.dataset.file;
    statusText.textContent = `Loading ${filename}`;
    try {
        const r = await fetch(`/static/examples/${filename}`);
        if (!r.ok) throw new Error('Could not load example');
        const blob = await r.blob();
        const file = new File([blob], filename, { type: 'text/plain' });
        setFile(file);
    } catch (e) {
        alert('Failed to load example: ' + e.message);
    }
});

// ===== Reset =====
$('resetBtn').addEventListener('click', () => {
    if (confirm('Reset session? This clears the chat and uploaded file.')) location.reload();
});

// ===== Chat =====
function enableInput() {
    userInput.disabled = false;
    sendBtn.disabled = false;
    userInput.focus();
    userInput.placeholder = currentFile ? 'Describe the placement you want...' : 'Upload a .def file to begin...';
}

userInput.addEventListener('input', () => {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 100) + 'px';
});

userInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
sendBtn.addEventListener('click', sendMessage);

document.querySelectorAll('.quick-action').forEach(btn => {
    btn.addEventListener('click', () => {
        if (!currentFile) { alert('Upload a .def file first'); return; }
        userInput.value = btn.dataset.msg;
        sendMessage();
    });
});

function addUserMessage(text) {
    if (welcome) welcome.style.display = 'none';
    const msg = document.createElement('div');
    msg.className = 'msg user';
    msg.innerHTML = `<div class="avatar">HN</div><div class="bubble">${escapeHtml(text)}</div>`;
    chatBody.appendChild(msg);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function addAIMessage(html, files = null) {
    if (welcome) welcome.style.display = 'none';
    const msg = document.createElement('div');
    msg.className = 'msg ai';
    let filesHtml = '';
    if (files && files.length) {
        filesHtml = '<div class="file-attachments">' + files.map(f =>
            `<a class="file-attach" href="${f.url}" download="${f.name}">
                <span class="kind">${f.kind || 'FILE'}</span>
                <span class="name">${escapeHtml(f.name)}</span>
                <span class="size">${f.size || ''}</span>
            </a>`
        ).join('') + '</div>';
    }
    msg.innerHTML = `<div class="avatar">SC</div><div class="bubble">${html}${filesHtml}</div>`;
    chatBody.appendChild(msg);
    chatBody.scrollTop = chatBody.scrollHeight;
    return msg;
}

function addTyping() {
    const msg = document.createElement('div');
    msg.className = 'msg ai';
    msg.id = 'typing-msg';
    msg.innerHTML = `<div class="avatar">SC</div><div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>`;
    chatBody.appendChild(msg);
    chatBody.scrollTop = chatBody.scrollHeight;
    return msg;
}

function removeTyping() {
    const t = $('typing-msg');
    if (t) t.remove();
}

function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;
    if (!currentFile && !sessionId) { alert('Upload a .def file first'); return; }

    addUserMessage(text);
    userInput.value = '';
    userInput.style.height = 'auto';
    userInput.disabled = true;
    sendBtn.disabled = true;
    chatStatus.classList.remove('online');
    chatStatus.classList.add('thinking');
    statusText.textContent = 'Placing';
    addTyping();

    try {
        let resp;
        if (!sessionId) {
            const fd = new FormData();
            fd.append('file', currentFile);
            fd.append('message', text);
            resp = await fetch('/api/copilot/start', { method: 'POST', body: fd });
        } else {
            const fd = new FormData();
            fd.append('session_id', sessionId);
            fd.append('message', text);
            resp = await fetch('/api/copilot/chat', { method: 'POST', body: fd });
        }
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: 'Server error' }));
            if (resp.status === 404 && currentFile) {
                sessionId = null;
                const fd = new FormData();
                fd.append('file', currentFile);
                fd.append('message', text);
                resp = await fetch('/api/copilot/start', { method: 'POST', body: fd });
            }
            if (!resp.ok) throw new Error(err.detail || 'Server error');
        }
        const data = await resp.json();
        sessionId = data.session_id;
        localStorage.setItem('chipmind_session', sessionId);
        removeTyping();
        renderTurn(data);
    } catch (err) {
        removeTyping();
        addAIMessage(`<p><strong>Error:</strong> ${escapeHtml(err.message)}</p>`);
        statusText.textContent = 'Error';
    } finally {
        userInput.disabled = false;
        sendBtn.disabled = false;
        chatStatus.classList.remove('thinking');
        chatStatus.classList.add('online');
        userInput.focus();
    }
}

function renderTurn(data) {
    lastResult = data;

    if (data.n_cells) {
        $('statCells').textContent = data.n_cells.toLocaleString();
        $('statNets').textContent = data.n_nets.toLocaleString();
        $('chipPanel').classList.remove('hidden');
    }

    if (data.preference && data.preference.length === 5) {
        const labels = ['HPWL', 'Power', 'Area', 'Timing', 'Routing'];
        const list = $('prefList');
        list.innerHTML = data.preference.map((v, i) => `
            <div class="pref-row">
                <div class="pref-name">${labels[i]}</div>
                <div class="pref-track"><div class="pref-fill" style="width: ${(v * 100).toFixed(0)}%"></div></div>
                <div class="pref-pct">${(v * 100).toFixed(0)}%</div>
            </div>
        `).join('');
        $('prefPanel').classList.remove('hidden');
    }

    if (data.old_hpwl !== undefined && data.new_hpwl !== undefined && data.new_hpwl !== null) {
        $('metricOldHpwl').textContent = Number(data.old_hpwl).toLocaleString();
        $('metricNewHpwl').textContent = Number(data.new_hpwl).toLocaleString();
        $('metricImprovement').textContent = (data.improvement_pct >= 0 ? '+' : '') + data.improvement_pct.toFixed(1) + '%';
        $('metricPerNet').textContent = (data.new_hpwl / (data.n_nets || 1)).toFixed(1);
        $('metricsPanel').classList.remove('hidden');
    }

    // Update axis widget with current placement info
    if (data.components) {
        updateAxisWidget(data.components, data.die);
        // Also enable the interactive placement view (drag-to-re-place)
        if (data.die && data.components && currentFile) {
            setupInteractive(data.components, data.die, currentFile);
        }
    }

    // Build the per-turn file attachments (DEF + GDS)
    let files = [];
    const designName = (data.design_name || 'placed').replace(/\.def$/, '');

    if (data.placed_def) {
        const placedName = `${designName}_placed.def`;
        const defBlob = new Blob([data.placed_def], { type: 'text/plain' });
        const defUrl = URL.createObjectURL(defBlob);
        files.push({ name: placedName, url: defUrl, kind: 'DEF', size: formatSize(data.placed_def.length) });

        const report = generateReport(data);
        const reportBlob = new Blob([report], { type: 'text/markdown' });
        const reportUrl = URL.createObjectURL(reportBlob);
        const reportName = `${designName}_report.md`;
        files.push({ name: reportName, url: reportUrl, kind: 'MD', size: formatSize(report.length) });
    }

    if (data.gds_base64) {
        // base64 → Uint8Array → Blob (so the file saves correctly as binary)
        const bin = atob(data.gds_base64);
        const bytes = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
        const gdsBlob = new Blob([bytes], { type: 'application/octet-stream' });
        const gdsUrl = URL.createObjectURL(gdsBlob);
        const gdsName = data.gds_filename || `${designName}_placed.gds`;
        files.push({
            name: gdsName,
            url: gdsUrl,
            kind: 'GDS',
            size: data.gds_size_bytes ? formatSize(data.gds_size_bytes) : '',
        });

        // Mirror into the right-side download panel
        const dl = $('downloadGds');
        if (dl) {
            dl.href = gdsUrl;
            dl.download = gdsName;
            $('downloadGdsName').textContent = gdsName;
            $('downloadPanel').classList.remove('hidden');
        }
    }

    if (data.placed_def) {
        const placedName = `${designName}_placed.def`;
        $('downloadDef').href = files[0].url;
        $('downloadDef').download = placedName;
        $('downloadDefName').textContent = placedName;
        $('downloadPanel').classList.remove('hidden');
    }

    addAIMessage(data.reply || 'Done.', files);
    statusText.textContent = `Session ${data.turn_count || 1}`;
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}

function generateReport(data) {
    const lines = [];
    lines.push(`# Placement Report — ${data.design_name}`);
    lines.push(``);
    lines.push(`Date: ${new Date().toISOString()}`);
    lines.push(`Session: ${data.session_id}`);
    lines.push(``);
    lines.push(`## Metrics`);
    lines.push(``);
    lines.push(`| Metric | Value |`);
    lines.push(`|---|---|`);
    lines.push(`| Cells | ${data.n_cells?.toLocaleString() || '—'} |`);
    lines.push(`| Nets | ${data.n_nets?.toLocaleString() || '—'} |`);
    lines.push(`| Old HPWL (OpenROAD default) | ${data.old_hpwl?.toLocaleString() || '—'} |`);
    lines.push(`| New HPWL (SmallChip AI) | ${data.new_hpwl?.toLocaleString() || '—'} |`);
    lines.push(`| Improvement | ${data.improvement_pct?.toFixed(1) || '—'}% |`);
    lines.push(`| Per-net HPWL | ${((data.new_hpwl || 0) / (data.n_nets || 1)).toFixed(1)} µm |`);
    lines.push(``);
    if (data.preference) {
        lines.push(`## Preference vector`);
        lines.push(``);
        const labels = ['HPWL', 'Power', 'Area', 'Timing', 'Routing'];
        data.preference.forEach((v, i) => lines.push(`- ${labels[i]}: ${(v * 100).toFixed(0)}%`));
        lines.push(``);
    }
    lines.push(`## Analysis`);
    lines.push(``);
    lines.push((data.reply || 'See placement assistant output for analysis.').replace(/<[^>]+>/g, ''));
    lines.push(``);
    lines.push(`---`);
    lines.push(`Generated by SmallChip AI v0.3.0 · github.com/hnelabhotla-boop/smallchip-ai`);
    return lines.join('\n');
}

// ===== Axis widget (X / Y / Z) =====
//
// Click the axis widget to flip between a 2D top-down view (X / Y) and
// a 3D preview (X / Y / Z). The 3D preview is a static, side-on render
// of the placed cells — it shows the X axis (red), Y axis (green), and
// Z axis (blue) so the user can see how the cells occupy the 3D space.
//
// For full 3D rendering with metal-layer stacks, download the .gds
// and open it in KLayout / gds-viewer.com / OpenROAD.

const axis = {
    mode: '2d',  // '2d' or '3d'
    yaw: -0.4,
    pitch: 0.55,
    zoom: 1.0,
    dragging: false,
    dragStart: null,
};

function updateAxisWidget(components, die) {
    axis.components = components;
    axis.die = die;
    const canvas = $('axisCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    ctx.fillStyle = '#050505';
    ctx.fillRect(0, 0, w, h);
    if (!die) return;
    const dieW = die.x2 - die.x1 || 1;
    const dieH = die.y2 - die.y1 || 1;
    const cells = Object.values(components || {});
    if (cells.length === 0) return;

    const cx = (die.x1 + die.x2) / 2;
    const cy = (die.y1 + die.y2) / 2;
    const maxDim = Math.max(dieW, dieH);

    // Project: yaw rotates around Z, pitch tilts the view
    const cosY = Math.cos(axis.yaw), sinY = Math.sin(axis.yaw);
    const cosP = Math.cos(axis.pitch), sinP = Math.sin(axis.pitch);

    // Draw die outline (faint)
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    ctx.beginPath();
    const corners = [[die.x1, die.y1], [die.x2, die.y1], [die.x2, die.y2], [die.x1, die.y2]];
    corners.forEach(([x, y], i) => {
        const dx = x - cx, dy = y - cy;
        const xr = dx * cosY - dy * sinY;
        const yr = (dx * sinY + dy * cosY) * cosP;
        const sx = w / 2 + xr / maxDim * (w * 0.42) * axis.zoom;
        const sy = h / 2 + yr / maxDim * (h * 0.42) * axis.zoom;
        if (i === 0) ctx.moveTo(sx, sy); else ctx.lineTo(sx, sy);
    });
    ctx.closePath();
    ctx.stroke();

    // Draw cells (a few thousand is plenty for a preview)
    const stride = Math.max(1, Math.floor(cells.length / 3000));
    const cellPx = Math.max(1, (w * 0.012) * axis.zoom);
    for (let i = 0; i < cells.length; i += stride) {
        const c = cells[i];
        const dx = c.x - cx, dy = c.y - cy;
        const xr = dx * cosY - dy * sinY;
        const yr = (dx * sinY + dy * cosY) * cosP;
        const sx = w / 2 + xr / maxDim * (w * 0.42) * axis.zoom;
        const sy = h / 2 + yr / maxDim * (h * 0.42) * axis.zoom;
        // Color cells by depth (back = dim, front = bright)
        const depth = ((dx * cosY + dy * sinY) / maxDim + 0.5);
        const t = Math.max(0.2, Math.min(1, 0.4 + depth * 0.6));
        const r = Math.round(99 * t);
        const g = Math.round(102 * t);
        const b = Math.round(241 * t);
        ctx.fillStyle = `rgb(${r},${g},${b})`;
        ctx.fillRect(sx - cellPx / 2, sy - cellPx / 2, cellPx, cellPx);
    }

    // Draw axis triad (X red, Y green, Z blue) — bottom-left corner
    const ax = 30, ay = h - 30, al = 22;
    ctx.lineWidth = 2;
    // X axis — red
    ctx.strokeStyle = '#ef4444';
    ctx.beginPath(); ctx.moveTo(ax, ay);
    ctx.lineTo(ax + al * cosY, ay - al * sinY * cosP);
    ctx.stroke();
    // Y axis — green
    ctx.strokeStyle = '#22c55e';
    ctx.beginPath(); ctx.moveTo(ax, ay);
    ctx.lineTo(ax + al * sinY, ay + al * cosY * cosP);
    ctx.stroke();
    // Z axis — blue (always pointing up in 2D preview, tilted in 3D preview)
    ctx.strokeStyle = '#3b82f6';
    ctx.beginPath(); ctx.moveTo(ax, ay);
    ctx.lineTo(ax, ay - al * sinP);
    ctx.stroke();
    // Labels
    ctx.font = '10px "SF Mono", monospace';
    ctx.fillStyle = '#ef4444'; ctx.fillText('X', ax + al * cosY + 4, ay - al * sinY * cosP + 4);
    ctx.fillStyle = '#22c55e'; ctx.fillText('Y', ax + al * sinY + 4, ay + al * cosY * cosP + 4);
    ctx.fillStyle = '#3b82f6'; ctx.fillText('Z', ax + 4, ay - al * sinP - 4);

    // Mode label
    ctx.fillStyle = '#6b6b6b';
    ctx.font = '9px "SF Mono", monospace';
    ctx.fillText(axis.mode.toUpperCase(), w - 28, 12);
}

// ===== Interactive placement (drag a cell, neighborhood re-places) =====
const interactive = {
    components: null,    // current cell positions
    die: null,
    selectedCell: null,  // cell being dragged
    dragging: false,
    dragOffset: { x: 0, y: 0 },
    lastNeighborhood: null,  // last partial re-placement result
    lastFile: null,           // File object for re-submission
    highlightedCells: new Set(),  // cells in the last neighborhood
    movedCellNewPos: null,    // the actual position of the moved cell after partial re-place
};

function showInteractivePanel() {
    const panel = $('interactivePanel');
    if (panel) panel.style.display = '';
}

function setupInteractiveCanvas() {
    const canvas = $('interactiveCanvas');
    if (!canvas) return;
    const ro = new ResizeObserver(() => {
        canvas.width = canvas.clientWidth;
        canvas.height = canvas.clientHeight;
        if (interactive.components) drawInteractive();
    });
    ro.observe(canvas);
    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientHeight;

    canvas.addEventListener('mousedown', onInteractiveMouseDown);
    canvas.addEventListener('mousemove', onInteractiveMouseMove);
    canvas.addEventListener('mouseup', onInteractiveMouseUp);
    canvas.addEventListener('mouseleave', () => {
        if (interactive.dragging) {
            interactive.dragging = false;
            interactive.selectedCell = null;
        }
    });
}

function dieToCanvas(die, w, h) {
    if (!die) return null;
    const dieW = (die.x2 - die.x1) || 1;
    const dieH = (die.y2 - die.y1) || 1;
    const maxDim = Math.max(dieW, dieH);
    return (x, y) => ({
        cx: w / 2 + ((x - die.x1) / maxDim - 0.5) * (w * 0.9),
        cy: h / 2 + ((y - die.y1) / maxDim - 0.5) * (h * 0.9),
    });
}

function canvasToDie(cx, cy, die, w, h) {
    if (!die) return null;
    const dieW = (die.x2 - die.x1) || 1;
    const dieH = (die.y2 - die.y1) || 1;
    const maxDim = Math.max(dieW, dieH);
    return {
        x: die.x1 + ((cx / w - 0.5) / 0.9 + 0.5) * maxDim,
        y: die.y1 + ((cy / h - 0.5) / 0.9 + 0.5) * maxDim,
    };
}

function findCellAt(cx, cy) {
    if (!interactive.components) return null;
    const project = dieToCanvas(interactive.die, 9999, 9999);
    if (!project) return null;
    const w = $('interactiveCanvas').width;
    const h = $('interactiveCanvas').height;
    const projection = dieToCanvas(interactive.die, w, h);
    // Search by closest cell within click radius
    let best = null;
    let bestDist = 8;  // 8px click radius
    for (const [name, c] of Object.entries(interactive.components)) {
        const p = projection(c.x, c.y);
        const d = Math.hypot(p.cx - cx, p.cy - cy);
        if (d < bestDist) {
            bestDist = d;
            best = name;
        }
    }
    return best;
}

function drawInteractive() {
    const canvas = $('interactiveCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    ctx.fillStyle = '#050505';
    ctx.fillRect(0, 0, w, h);
    if (!interactive.components || !interactive.die) return;

    const projection = dieToCanvas(interactive.die, w, h);
    const cells = Object.entries(interactive.components);
    if (cells.length === 0) return;

    // Stride for large designs
    const stride = Math.max(1, Math.floor(cells.length / 1500));

    // Draw cells
    for (let i = 0; i < cells.length; i += stride) {
        const [name, c] = cells[i];
        const p = projection(c.x, c.y);
        const cellPx = Math.max(1, (w * 0.01));

        // Color: highlighted (in last neighborhood) = cyan, moved = bright cyan, default = blue
        if (name === interactive.selectedCell) {
            ctx.fillStyle = '#5fd97f';  // green for selected
        } else if (interactive.highlightedCells.has(name)) {
            ctx.fillStyle = '#4a9eff';  // blue for neighborhood
        } else {
            ctx.fillStyle = '#666';
        }
        ctx.fillRect(p.cx - cellPx/2, p.cy - cellPx/2, cellPx, cellPx);
    }

    // Draw die outline
    const corners = [
        [interactive.die.x1, interactive.die.y1],
        [interactive.die.x2, interactive.die.y1],
        [interactive.die.x2, interactive.die.y2],
        [interactive.die.x1, interactive.die.y2],
    ];
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    ctx.beginPath();
    corners.forEach(([x, y], i) => {
        const p = projection(x, y);
        if (i === 0) ctx.moveTo(p.cx, p.cy);
        else ctx.lineTo(p.cx, p.cy);
    });
    ctx.closePath();
    ctx.stroke();
}

function onInteractiveMouseDown(e) {
    if (!interactive.components) return;
    const rect = e.target.getBoundingClientRect();
    const cx = e.clientX - rect.left;
    const cy = e.clientY - rect.top;
    const cell = findCellAt(cx, cy);
    if (cell) {
        interactive.selectedCell = cell;
        interactive.dragging = true;
        // Compute offset between click and cell center
        const c = interactive.components[cell];
        const projection = dieToCanvas(interactive.die, rect.width, rect.height);
        const cellPos = projection(c.x, c.y);
        interactive.dragOffset = { x: cx - cellPos.cx, y: cy - cellPos.cy };
        drawInteractive();
        const status = $('interactiveStatus');
        if (status) {
            status.textContent = `Dragging "${cell}". Release to re-place neighborhood.`;
            status.classList.add('active');
        }
    }
}

function onInteractiveMouseMove(e) {
    if (!interactive.dragging) return;
    drawInteractive();
    // Draw the cell at the cursor position
    const rect = e.target.getBoundingClientRect();
    const cx = e.clientX - rect.left - interactive.dragOffset.x;
    const cy = e.clientY - rect.top - interactive.dragOffset.y;
    const canvas = $('interactiveCanvas');
    const ctx = canvas.getContext('2d');
    const cellPx = Math.max(2, (canvas.width * 0.014));
    ctx.fillStyle = '#5fd97f';
    ctx.fillRect(cx - cellPx/2, cy - cellPx/2, cellPx, cellPx);
    // Draw crosshair
    ctx.strokeStyle = '#5fd97f';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(cx - 8, cy);
    ctx.lineTo(cx + 8, cy);
    ctx.moveTo(cx, cy - 8);
    ctx.lineTo(cx, cy + 8);
    ctx.stroke();
}

async function onInteractiveMouseUp(e) {
    if (!interactive.dragging) return;
    interactive.dragging = false;
    const rect = e.target.getBoundingClientRect();
    const cx = e.clientX - rect.left - interactive.dragOffset.x;
    const cy = e.clientY - rect.top - interactive.dragOffset.y;
    const targetDie = canvasToDie(cx, cy, interactive.die, rect.width, rect.height);
    if (!targetDie || !interactive.lastFile) {
        interactive.selectedCell = null;
        drawInteractive();
        return;
    }

    const status = $('interactiveStatus');
    if (status) status.textContent = `Re-placing neighborhood around "${interactive.selectedCell}"...`;

    const form = new FormData();
    form.append('file', interactive.lastFile);
    form.append('moved_cell', interactive.selectedCell);
    form.append('target_x', targetDie.x);
    form.append('target_y', targetDie.y);

    try {
        const t0 = performance.now();
        const r = await fetch('/api/place_partial', { method: 'POST', body: form });
        const elapsedTotal = performance.now() - t0;
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        interactive.highlightedCells = new Set(data.neighborhood_cells);
        // Update positions
        for (const [name, pos] of Object.entries(data.new_positions)) {
            if (interactive.components[name]) {
                interactive.components[name].x = pos.x;
                interactive.components[name].y = pos.y;
            }
        }
        drawInteractive();
        if (status) {
            status.textContent = `Re-placed ${data.neighborhood_size} cells in ${data.elapsed_ms.toFixed(0)}ms (round-trip ${elapsedTotal.toFixed(0)}ms). HPWL: ${interactive.selectedCell} moved to (${targetDie.x.toFixed(0)}, ${targetDie.y.toFixed(0)}).`;
            status.classList.add('active');
        }
    } catch (err) {
        if (status) status.textContent = `Error: ${err.message}`;
    }
    interactive.selectedCell = null;
}

function setupInteractive(components, die, file) {
    interactive.components = components;
    interactive.die = die;
    interactive.lastFile = file;
    interactive.highlightedCells = new Set();
    showInteractivePanel();
    setupInteractiveCanvas();
    drawInteractive();
}

function bindAxisWidget() {
    const canvas = $('axisCanvas');
    if (!canvas) return;
    const ro = new ResizeObserver(() => {
        canvas.width = canvas.clientWidth;
        canvas.height = canvas.clientHeight;
        if (axis.components) updateAxisWidget(axis.components, axis.die);
    });
    ro.observe(canvas);
    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientHeight;

    // Drag to rotate
    canvas.addEventListener('mousedown', e => {
        axis.dragging = true;
        axis.dragStart = { x: e.clientX, y: e.clientY, yaw: axis.yaw, pitch: axis.pitch };
    });
    canvas.addEventListener('mousemove', e => {
        if (!axis.dragging) return;
        const dx = e.clientX - axis.dragStart.x;
        const dy = e.clientY - axis.dragStart.y;
        axis.yaw = axis.dragStart.yaw - dx * 0.005;
        axis.pitch = Math.max(0.05, Math.min(1.5, axis.dragStart.pitch + dy * 0.005));
        updateAxisWidget(axis.components, axis.die);
    });
    const stop = () => { axis.dragging = false; };
    canvas.addEventListener('mouseup', stop);
    canvas.addEventListener('mouseleave', stop);
    canvas.addEventListener('wheel', e => {
        e.preventDefault();
        axis.zoom *= e.deltaY < 0 ? 1.1 : 0.9;
        axis.zoom = Math.max(0.3, Math.min(5, axis.zoom));
        updateAxisWidget(axis.components, axis.die);
    }, { passive: false });

    // 2D / 3D toggle button
    document.querySelectorAll('#axisControls .axis-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            if (mode === '2d') { axis.mode = '2d'; axis.pitch = 0.05; }
            else if (mode === '3d') { axis.mode = '3d'; axis.pitch = 0.85; axis.yaw = -0.6; }
            else if (mode === 'reset') { axis.yaw = -0.4; axis.pitch = 0.55; axis.zoom = 1.0; }
            document.querySelectorAll('#axisControls .axis-btn').forEach(b => {
                if (b.dataset.mode !== 'reset') b.classList.remove('active');
            });
            if (mode !== 'reset') btn.classList.add('active');
            updateAxisWidget(axis.components, axis.die);
        });
    });
}

bindAxisWidget();

// ===== Restore session =====
try {
    const saved = localStorage.getItem('chipmind_session');
    if (saved) {
        sessionId = saved;
        statusText.textContent = 'Resumed';
    }
} catch (e) {}

// ===== Server health ping =====
async function ping() {
    try {
        const r = await fetch('/api/health');
        if (r.ok) chatStatus.classList.add('online');
    } catch (e) {
        chatStatus.classList.remove('online');
    }
}
ping();
setInterval(ping, 30000);
