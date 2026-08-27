// SmallChip AI — modern unified app
let currentFile = null;
let sessionId = null;
let lastResult = null;
let currentDesign = null;

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
const fileInfo = $('fileInfo');
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
    fileName.textContent = '✓ ' + file.name;
    fileMeta.textContent = `${(file.size / 1024).toFixed(1)} KB`;
    fileInfo.classList.remove('hidden');
    statusText.textContent = 'Chip loaded — type a request or pick a quick action';
    chatStatus.classList.add('online');
    enableInput();
}

examples.addEventListener('click', async e => {
    if (!e.target.dataset.file) return;
    const filename = e.target.dataset.file;
    statusText.textContent = `Loading ${filename}...`;
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
    userInput.placeholder = currentFile ? 'Type your message...' : 'Upload a .def file first...';
}

userInput.addEventListener('input', () => {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
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
    msg.innerHTML = `
        <div class="avatar">H</div>
        <div class="bubble">${escapeHtml(text)}</div>
    `;
    chatBody.appendChild(msg);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function addAIMessage(html, files = null) {
    if (welcome) welcome.style.display = 'none';
    const msg = document.createElement('div');
    msg.className = 'msg ai';
    let filesHtml = '';
    if (files && files.length) {
        filesHtml = '<div class="files">' + files.map(f =>
            `<a class="file-chip" href="${f.url}" download="${f.name}">⬇ ${escapeHtml(f.name)}</a>`
        ).join('') + '</div>';
    }
    msg.innerHTML = `
        <div class="avatar">AI</div>
        <div class="bubble">${html}${filesHtml}</div>
    `;
    chatBody.appendChild(msg);
    chatBody.scrollTop = chatBody.scrollHeight;
    return msg;
}

function addTyping() {
    const msg = document.createElement('div');
    msg.className = 'msg ai';
    msg.id = 'typing-msg';
    msg.innerHTML = `
        <div class="avatar">AI</div>
        <div class="bubble"><div class="typing-bubble"><span></span><span></span><span></span></div></div>
    `;
    chatBody.appendChild(msg);
    chatBody.scrollTop = chatBody.scrollHeight;
    return msg;
}

function removeTyping() {
    const t = $('typing-msg');
    if (t) t.remove();
}

function escapeHtml(s) {
    return s.replace(/[&<>"']/g, c => ({
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
    statusText.textContent = 'Placing chip...';
    const typing = addTyping();

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
        addAIMessage(`<strong>⚠️ Error:</strong> ${escapeHtml(err.message)}`);
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
    currentDesign = data.design_name;

    // Update chip info
    if (data.n_cells) {
        $('statCells').textContent = data.n_cells.toLocaleString();
        $('statNets').textContent = data.n_nets.toLocaleString();
        $('chipPanel').classList.remove('hidden');
    }

    // Update preference bars
    if (data.preference && data.preference.length === 5) {
        const labels = ['HPWL', 'Power', 'Area', 'Timing', 'Routing'];
        const list = $('prefList');
        list.innerHTML = data.preference.map((v, i) => `
            <div style="display: flex; align-items: center; gap: 8px; font-size: 12px;">
                <div style="width: 60px; color: var(--text-muted);">${labels[i]}</div>
                <div style="flex: 1; height: 6px; background: var(--surface-2); border-radius: 3px; overflow: hidden;">
                    <div style="width: ${(v * 100).toFixed(0)}%; height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-2)); transition: width 0.4s;"></div>
                </div>
                <div style="width: 36px; text-align: right; font-weight: 600;">${(v * 100).toFixed(0)}%</div>
            </div>
        `).join('');
        $('prefPanel').classList.remove('hidden');
    }

    // Update metrics
    if (data.old_hpwl !== undefined && data.new_hpwl !== undefined) {
        $('metricOldHpwl').textContent = data.old_hpwl.toLocaleString();
        $('metricNewHpwl').textContent = data.new_hpwl.toLocaleString();
        $('metricImprovement').textContent = data.improvement_pct.toFixed(1) + '%';
        $('metricPerNet').textContent = (data.new_hpwl / (data.n_nets || 1)).toFixed(1) + ' µm';
        $('metricsPanel').classList.remove('hidden');
        $('vizEmpty').classList.add('hidden');
    }

    // Update download buttons
    if (data.placed_def) {
        const blob = new Blob([data.placed_def], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const placedName = (data.design_name || 'placed').replace(/\.def$/, '') + '_smallchip.def';
        $('downloadBtn').href = url;
        $('downloadBtn').download = placedName;
        $('downloadBtn').classList.remove('disabled');
        $('downloadBtn').textContent = `⬇ ${placedName}`;
        $('downloadArea').classList.remove('hidden');

        // Generate a report file
        const report = generateReport(data);
        const reportBlob = new Blob([report], { type: 'text/markdown' });
        const reportUrl = URL.createObjectURL(reportBlob);
        $('downloadReportBtn').href = reportUrl;
        $('downloadReportBtn').download = placedName.replace('.def', '_report.md');
        $('downloadReportBtn').classList.remove('disabled');
    }

    // Update visualization
    if (data.components) {
        visualize(data.components, data.die, data.design_name);
    }

    // Add the AI reply
    const replyHtml = data.reply || 'Done.';
    addAIMessage(replyHtml);

    statusText.textContent = `Session active — turn ${data.turn_count || 1}`;
}

function generateReport(data) {
    const lines = [];
    lines.push(`# SmallChip AI — Placement Report`);
    lines.push(``);
    lines.push(`**Design:** ${data.design_name}`);
    lines.push(`**Date:** ${new Date().toISOString()}`);
    lines.push(`**Session:** ${data.session_id}`);
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
        data.preference.forEach((v, i) => lines.push(`- **${labels[i]}:** ${(v * 100).toFixed(0)}%`));
        lines.push(``);
    }
    lines.push(`## Analysis`);
    lines.push(``);
    lines.push(data.reply || 'See SmallChip AI co-pilot output for analysis.');
    lines.push(``);
    lines.push(`---`);
    lines.push(`*Generated by SmallChip AI v0.2.0 — github.com/hnelabhotla-boop/smallchip-ai*`);
    return lines.join('\n');
}

// ===== Visualization =====
const canvas = $('placementCanvas');
const ctx = canvas.getContext('2d');

function visualize(components, die, name) {
    if (!components || !die) return;
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#0d1117';
    ctx.fillRect(0, 0, w, h);

    const xs = Object.values(components).map(c => c.x);
    const ys = Object.values(components).map(c => c.y);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const dieW = Math.max(maxX - minX, 1);
    const dieH = Math.max(maxY - minY, 1);
    const pad = 8;
    const scale = Math.min((w - 2 * pad) / dieW, (h - 2 * pad) / dieH);

    // Draw die outline
    ctx.strokeStyle = '#30363d';
    ctx.lineWidth = 1;
    ctx.strokeRect(pad, pad, dieW * scale, dieH * scale);

    // Draw cells
    ctx.fillStyle = '#7ee787';
    const cellSize = Math.max(1.5, Math.min(3, scale * 0.4));
    const vals = Object.values(components);
    const maxN = Math.min(vals.length, 2000);
    for (let i = 0; i < maxN; i++) {
        const c = vals[i];
        const cx = pad + (c.x - minX) * scale;
        const cy = pad + (c.y - minY) * scale;
        ctx.fillRect(cx - cellSize/2, cy - cellSize/2, cellSize, cellSize);
    }
    if (vals.length > maxN) {
        ctx.fillStyle = '#7d8590';
        ctx.font = '11px -apple-system, sans-serif';
        ctx.fillText(`(showing ${maxN} of ${vals.length} cells)`, pad, h - pad);
    }
}

// ===== Restore session =====
try {
    const saved = localStorage.getItem('chipmind_session');
    if (saved) {
        sessionId = saved;
        statusText.textContent = 'Resumed session — re-upload your .def to continue';
    }
} catch (e) {}

// ===== Server-sent status (online indicator) =====
async function ping() {
    try {
        const r = await fetch('/api/health', { method: 'GET' });
        if (r.ok) {
            chatStatus.classList.add('online');
        }
    } catch (e) {
        chatStatus.classList.remove('online');
    }
}
ping();
setInterval(ping, 30000);
