// SmallChip AI — professional chip placement co-pilot
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
                <span class="icon">↓</span>
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

    if (data.old_hpwl !== undefined && data.new_hpwl !== undefined) {
        $('metricOldHpwl').textContent = data.old_hpwl.toLocaleString();
        $('metricNewHpwl').textContent = data.new_hpwl.toLocaleString();
        $('metricImprovement').textContent = (data.improvement_pct >= 0 ? '+' : '') + data.improvement_pct.toFixed(1) + '%';
        $('metricPerNet').textContent = (data.new_hpwl / (data.n_nets || 1)).toFixed(1);
        $('metricsPanel').classList.remove('hidden');
        $('vizEmpty').classList.add('hidden');
    }

    if (data.placed_def) {
        const blob = new Blob([data.placed_def], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const placedName = (data.design_name || 'placed').replace(/\.def$/, '') + '_placed.def';
        const defSize = formatSize(data.placed_def.length);
        $('downloadDef').href = url;
        $('downloadDef').download = placedName;
        $('downloadDefName').textContent = placedName;
        $('downloadDef').querySelector('.size') && ($('downloadDef').querySelector('.size').textContent = defSize);

        const report = generateReport(data);
        const reportBlob = new Blob([report], { type: 'text/markdown' });
        const reportUrl = URL.createObjectURL(reportBlob);
        const reportName = placedName.replace('.def', '_report.md');
        $('downloadReport').href = reportUrl;
        $('downloadReport').download = reportName;
        $('downloadReportName').textContent = reportName;
        $('downloadPanel').classList.remove('hidden');
    }

    if (data.components) {
        visualize(data.components, data.die, data.design_name);
    }

    addAIMessage(data.reply || 'Done.');
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
    lines.push(`Generated by SmallChip AI v0.2.0 · github.com/hnelabhotla-boop/smallchip-ai`);
    return lines.join('\n');
}

// ===== Visualization =====
const canvas = $('placementCanvas');
const ctx = canvas.getContext('2d');

function visualize(components, die, name) {
    if (!components || !die) return;
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, w, h);

    const xs = Object.values(components).map(c => c.x);
    const ys = Object.values(components).map(c => c.y);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const dieW = Math.max(maxX - minX, 1);
    const dieH = Math.max(maxY - minY, 1);
    const pad = 8;
    const scale = Math.min((w - 2 * pad) / dieW, (h - 2 * pad) / dieH);

    ctx.strokeStyle = '#262626';
    ctx.lineWidth = 1;
    ctx.strokeRect(pad, pad, dieW * scale, dieH * scale);

    ctx.fillStyle = '#6366f1';
    const cellSize = Math.max(1, Math.min(2.5, scale * 0.3));
    const vals = Object.values(components);
    const maxN = Math.min(vals.length, 2500);
    for (let i = 0; i < maxN; i++) {
        const c = vals[i];
        const cx = pad + (c.x - minX) * scale;
        const cy = pad + (c.y - minY) * scale;
        ctx.fillRect(cx - cellSize/2, cy - cellSize/2, cellSize, cellSize);
    }
    if (vals.length > maxN) {
        ctx.fillStyle = '#6b6b6b';
        ctx.font = '10px Inter, sans-serif';
        ctx.fillText(`${maxN.toLocaleString()} of ${vals.length.toLocaleString()} cells shown`, pad, h - pad);
    }
}

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
