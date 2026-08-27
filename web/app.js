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

    if (data.old_hpwl !== undefined && data.new_hpwl !== undefined && data.new_hpwl !== null) {
        $('metricOldHpwl').textContent = Number(data.old_hpwl).toLocaleString();
        $('metricNewHpwl').textContent = Number(data.new_hpwl).toLocaleString();
        $('metricImprovement').textContent = (data.improvement_pct >= 0 ? '+' : '') + data.improvement_pct.toFixed(1) + '%';
        $('metricPerNet').textContent = (data.new_hpwl / (data.n_nets || 1)).toFixed(1);
        $('metricsPanel').classList.remove('hidden');
        $('vizEmpty').classList.add('hidden');
    }

    // Build the per-turn inline files for the AI message bubble
    let files = [];
    if (data.placed_def) {
        const placedName = (data.design_name || 'placed').replace(/\.def$/, '') + '_placed.def';
        const defBlob = new Blob([data.placed_def], { type: 'text/plain' });
        const defUrl = URL.createObjectURL(defBlob);
        files.push({ name: placedName, url: defUrl, kind: 'def', size: formatSize(data.placed_def.length) });

        const report = generateReport(data);
        const reportBlob = new Blob([report], { type: 'text/markdown' });
        const reportUrl = URL.createObjectURL(reportBlob);
        const reportName = placedName.replace('.def', '_report.md');
        files.push({ name: reportName, url: reportUrl, kind: 'report', size: formatSize(report.length) });
    }

    if (data.placed_def) {
        // Mirror the latest files into the right-side panel
        const placedName = (data.design_name || 'placed').replace(/\.def$/, '') + '_placed.def';
        $('downloadDef').href = files[0].url;
        $('downloadDef').download = placedName;
        $('downloadDefName').textContent = placedName;
        if (files[1]) {
            $('downloadReport').href = files[1].url;
            $('downloadReport').download = files[1].name;
            $('downloadReportName').textContent = files[1].name;
        }
        $('downloadPanel').classList.remove('hidden');
    }

    if (data.components) {
        visualize(data.components, data.die, data.design_name);
        if (data.intent === 'request' || data.intent === undefined) {
            // also push the new components into 3D viz, keeping the previous
            // "old" placement in memory for side-by-side comparison
            if (window.__viz3d && window.__viz3d.pushPlacement) {
                window.__viz3d.pushPlacement(data.components, data.design_name);
            }
        }
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
    lines.push(`Generated by SmallChip AI v0.2.0 · github.com/hnelabhotla-boop/smallchip-ai`);
    return lines.join('\n');
}

// ===== Visualization =====
// 3D viewer: two side-by-side Three.js scenes (Before / After).
// Before = original placement from uploaded DEF.
// After  = current placement from V3 GAT.

const __viz3d = {
    before: null,
    after: null,
    setMode(mode) {
        if (this.before) this.before.setMode(mode);
        if (this.after) this.after.setMode(mode);
    },
    resetCameras() {
        if (this.before) this.before.resetCamera();
        if (this.after) this.after.resetCamera();
    },
    pushPlacement(components, name) {
        // First request: also seed the "Before" with the original positions
        if (!this.before) {
            const original = lastResult && lastResult.original_components;
            const beforeHpwl = lastResult && lastResult.old_hpwl;
            if (original) {
                this.before = new Viz3D('viz3dBefore', original, lastResult.die, beforeHpwl, 'BEFORE');
            }
        }
        const afterHpwl = lastResult && lastResult.new_hpwl;
        this.after = new Viz3D('viz3dAfter', components, lastResult && lastResult.die, afterHpwl, 'AFTER');
        $('vizAfterHpwl').textContent = afterHpwl ? Number(afterHpwl).toLocaleString() : '—';
        if (this.before) $('vizBeforeHpwl').textContent = this.before.hpwl ? Number(this.before.hpwl).toLocaleString() : '—';
    },
    showOriginal(originalComponents, die, hpwl) {
        if (this.before) this.before.dispose();
        this.before = new Viz3D('viz3dBefore', originalComponents, die, hpwl, 'BEFORE');
        $('vizBeforeHpwl').textContent = hpwl ? Number(hpwl).toLocaleString() : '—';
    }
};
window.__viz3d = __viz3d;

class Viz3D {
    constructor(containerId, components, die, hpwl, label) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;
        // Clean up any previous canvas
        const prev = this.container.querySelector('canvas');
        if (prev) prev.remove();
        // Also keep the .viz3d-label and .viz3d-stats in place
        this.components = components || {};
        this.die = die || null;
        this.hpwl = hpwl;
        this.label = label;
        this.mode = 'layout';
        this.useWebGL = false;
        this._isDragging = false;
        this._dragStart = null;
        this._cameraYaw = -0.6;  // -PI/2 = top-down, 0 = side view
        this._cameraPitch = 0.9;  // tilt angle
        this._cameraZoom = 1.0;
        // Try WebGL; if anything fails, use 2D canvas fallback
        try {
            if (typeof THREE === 'undefined') throw new Error('THREE not loaded');
            // Quick WebGL probe
            const probe = document.createElement('canvas');
            const gl = probe.getContext('webgl2') || probe.getContext('webgl')
                    || probe.getContext('experimental-webgl');
            if (!gl) throw new Error('WebGL not supported by this browser/viewer');
            this._setupScene();
            this._populate();
            this._start();
            this.useWebGL = true;
        } catch (e) {
            console.warn(`[Viz3D:${label}] WebGL unavailable, using 2D fallback:`, e.message);
            this._setup2D();
            this._populate2D();
            this.useWebGL = false;
        }
    }

    // ---------------- 2D fallback ----------------
    _setup2D() {
        const w = this.container.clientWidth || 200;
        const h = this.container.clientHeight || 200;
        const canvas = document.createElement('canvas');
        canvas.width = w; canvas.height = h;
        canvas.style.cursor = 'grab';
        canvas.addEventListener('mousedown', e => {
            this._isDragging = true;
            this._dragStart = { x: e.clientX, y: e.clientY, yaw: this._cameraYaw, pitch: this._cameraPitch };
            canvas.style.cursor = 'grabbing';
        });
        canvas.addEventListener('mousemove', e => {
            if (!this._isDragging) return;
            const dx = e.clientX - this._dragStart.x;
            const dy = e.clientY - this._dragStart.y;
            this._cameraYaw = this._dragStart.yaw - dx * 0.005;
            this._cameraPitch = Math.max(0.05, Math.min(1.5, this._dragStart.pitch + dy * 0.005));
            this._populate2D();
        });
        const stop = () => { this._isDragging = false; canvas.style.cursor = 'grab'; };
        canvas.addEventListener('mouseup', stop);
        canvas.addEventListener('mouseleave', stop);
        canvas.addEventListener('wheel', e => {
            e.preventDefault();
            this._cameraZoom *= e.deltaY < 0 ? 1.1 : 0.9;
            this._cameraZoom = Math.max(0.3, Math.min(5, this._cameraZoom));
            this._populate2D();
        }, { passive: false });
        this._canvas2d = canvas;
        this.container.appendChild(canvas);
        const ro = new ResizeObserver(() => {
            const w2 = this.container.clientWidth, h2 = this.container.clientHeight;
            if (w2 === 0 || h2 === 0) return;
            canvas.width = w2; canvas.height = h2;
            this._populate2D();
        });
        ro.observe(this.container);
        this._ro2d = ro;
    }

    _populate2D() {
        const canvas = this._canvas2d;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const w = canvas.width, h = canvas.height;
        ctx.fillStyle = '#050505';
        ctx.fillRect(0, 0, w, h);
        if (!this.die) return;
        const dieW = this.die.x2 - this.die.x1 || 1;
        const dieH = this.die.y2 - this.die.y1 || 1;
        const cells = Object.values(this.components);
        if (cells.length === 0) return;
        // Isometric projection: yaw rotates around Z; pitch tilts the view.
        const yaw = this._cameraYaw;
        const pitch = this._cameraPitch;
        const cosY = Math.cos(yaw), sinY = Math.sin(yaw);
        const cosP = Math.cos(pitch), sinP = Math.sin(pitch);
        // Project each cell to (sx, sy)
        const points = [];
        let minSx = Infinity, minSy = Infinity, maxSx = -Infinity, maxSy = -Infinity;
        for (let i = 0; i < cells.length; i++) {
            const c = cells[i];
            // First center die coords
            const x = c.x - (this.die.x1 + this.die.x2) / 2;
            const y = c.y - (this.die.y1 + this.die.y2) / 2;
            // Rotate around Z by yaw (in plan view), then tilt by pitch
            const xr = x * cosY - y * sinY;
            const yr = x * sinY + y * cosY;
            // Tilt: y' = y*cos(pitch), z = y*sin(pitch)
            const sx = xr;
            const sy = yr * cosP;
            // z (height) is used to color and offset y in screen space
            const h01 = (Math.sin((i + 1) * 9.7) * 0.5 + 0.5);
            const h = this.mode === 'height' ? h01 * dieW * 0.15 : dieW * 0.02;
            const screenY = sy - h * sinP;
            points.push({ sx, screenY, h01, h });
            if (sx < minSx) minSx = sx;
            if (sx > maxSx) maxSx = sx;
            if (screenY < minSy) minSy = screenY;
            if (screenY > maxSy) maxSy = screenY;
        }
        const pw = maxSx - minSx || 1;
        const ph = maxSy - minSy || 1;
        const scale = Math.min((w - 16) / pw, (h - 16) / ph) * this._cameraZoom;
        const ox = w / 2 - (minSx + maxSx) / 2 * scale;
        const oy = h / 2 - (minSy + maxSy) / 2 * scale;
        // Draw die outline (faint)
        ctx.strokeStyle = '#222';
        ctx.lineWidth = 1;
        const diePts = [[this.die.x1, this.die.y1], [this.die.x2, this.die.y1],
                        [this.die.x2, this.die.y2], [this.die.x1, this.die.y2]];
        ctx.beginPath();
        diePts.forEach(([x, y], i) => {
            const cx = x - (this.die.x1 + this.die.x2) / 2;
            const cy = y - (this.die.y1 + this.die.y2) / 2;
            const xr = cx * cosY - cy * sinY;
            const yr = cx * sinY + cy * cosY;
            const sx = ox + xr * scale;
            const sy = oy + yr * cosP * scale;
            if (i === 0) ctx.moveTo(sx, sy); else ctx.lineTo(sx, sy);
        });
        ctx.closePath();
        ctx.stroke();
        // Draw cells sorted back-to-front (smaller screenY first)
        points.sort((a, b) => a.screenY - b.screenY);
        const cellSize = Math.max(1, scale * 0.012);
        for (let i = 0; i < points.length; i++) {
            const p = points[i];
            const sx = ox + p.sx * scale;
            const sy = oy + p.screenY * scale;
            const t = p.h01;
            // Indigo -> warm
            const r = Math.round(99 + t * 80);
            const g = Math.round(102 - t * 30);
            const b = Math.round(241 - t * 100);
            ctx.fillStyle = `rgb(${r},${g},${b})`;
            const size = cellSize * (this.mode === 'height' ? (1 + t * 2) : 1);
            ctx.fillRect(sx - size / 2, sy - size / 2, size, size);
        }
        // Footer: cell count
        ctx.fillStyle = '#6b6b6b';
        ctx.font = '9px "SF Mono", monospace';
        ctx.fillText(`${cells.length.toLocaleString()} cells`, 4, h - 4);
    }

    // ---------------- 3D (WebGL) ----------------
    _setupScene() {
        const w = this.container.clientWidth || 200;
        const h = this.container.clientHeight || 200;
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x050505);
        const cam = this.camera = new THREE.PerspectiveCamera(45, w / h, 1, 1e9);
        cam.position.set(0, -800, 600);
        cam.up.set(0, 0, 1);
        cam.lookAt(0, 0, 0);
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setPixelRatio(window.devicePixelRatio || 1);
        this.renderer.setSize(w, h);
        this.container.appendChild(this.renderer.domElement);
        this.controls = new THREE.OrbitControls(cam, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.08;
        this.controls.screenSpacePanning = false;
        // Lighting
        const amb = new THREE.AmbientLight(0xffffff, 0.55);
        this.scene.add(amb);
        const dir = new THREE.DirectionalLight(0xffffff, 0.55);
        dir.position.set(1, 1, 2);
        this.scene.add(dir);
        const dir2 = new THREE.DirectionalLight(0x818cf8, 0.35);
        dir2.position.set(-1, -1, 1);
        this.scene.add(dir2);
        // Resize hook
        const ro = new ResizeObserver(() => this._resize());
        ro.observe(this.container);
        this._ro = ro;
    }

    _populate() {
        if (!this.die) return;
        const dieW = this.die.x2 - this.die.x1;
        const dieH = this.die.y2 - this.die.y1;
        const cx = (this.die.x1 + this.die.x2) / 2;
        const cy = (this.die.y1 + this.die.y2) / 2;
        // Die as a flat plane (rotated to lie in X-Y)
        const planeGeo = new THREE.PlaneGeometry(dieW, dieH);
        const planeMat = new THREE.MeshBasicMaterial({
            color: 0x141414, side: THREE.DoubleSide, transparent: true, opacity: 0.85,
        });
        const plane = new THREE.Mesh(planeGeo, planeMat);
        plane.position.set(cx, cy, -0.5);
        this.scene.add(plane);
        // Die outline
        const edgeGeo = new THREE.EdgesGeometry(planeGeo);
        const edge = new THREE.LineSegments(edgeGeo, new THREE.LineBasicMaterial({ color: 0x333333 }));
        edge.position.copy(plane.position);
        this.scene.add(edge);
        // Cells
        const cells = Object.values(this.components);
        if (cells.length === 0) return;
        // Stable per-cell height value
        const heights = cells.map((_, i) => Math.sin((i + 1) * 9.7) * 0.5 + 0.5);
        // Geometry: instanced for performance
        const baseW = Math.max(dieW, dieH) * 0.012;
        const baseH = Math.max(dieW, dieH) * 0.012;
        const baseD = Math.max(dieW, dieH) * 0.05;
        const cellGeo = new THREE.BoxGeometry(baseW, baseH, baseD);
        const cellMat = new THREE.MeshLambertMaterial({ color: 0x6366f1 });
        const inst = new THREE.InstancedMesh(cellGeo, cellMat, cells.length);
        const dummy = new THREE.Object3D();
        const colorAttr = new Float32Array(cells.length * 3);
        for (let i = 0; i < cells.length; i++) {
            const c = cells[i];
            dummy.position.set(c.x, c.y, baseD / 2);
            const h = this.mode === 'height' ? baseD * (0.3 + heights[i] * 2.5) : baseD * 0.4;
            dummy.scale.set(1, 1, h / baseD);
            dummy.updateMatrix();
            inst.setMatrixAt(i, dummy.matrix);
            const t = heights[i];
            const r = 0.39 + t * 0.4;
            const g = 0.40 - t * 0.2;
            const b = 1.00 - t * 0.5;
            colorAttr[i * 3] = r; colorAttr[i * 3 + 1] = g; colorAttr[i * 3 + 2] = b;
        }
        inst.instanceColor = new THREE.InstancedBufferAttribute(colorAttr, 3);
        inst.instanceColor.needsUpdate = true;
        this.scene.add(inst);
        this._inst = inst;
        this._heights = heights;
        this._baseD = baseD;
        // Frame the camera on the die
        const maxDim = Math.max(dieW, dieH);
        this.camera.position.set(0, -maxDim * 1.1, maxDim * 0.7);
        this.controls.target.set(cx, cy, 0);
        this.controls.update();
    }

    setMode(mode) {
        if (mode === 'reset') { this.resetCamera(); return; }
        this.mode = mode;
        if (this.useWebGL && this._inst) {
            const dummy = new THREE.Object3D();
            const cells = Object.values(this.components);
            for (let i = 0; i < cells.length; i++) {
                const c = cells[i];
                dummy.position.set(c.x, c.y, this._baseD / 2);
                const h = (mode === 'height')
                    ? this._baseD * (0.3 + this._heights[i] * 2.5)
                    : this._baseD * 0.4;
                dummy.scale.set(1, 1, h / this._baseD);
                dummy.updateMatrix();
                this._inst.setMatrixAt(i, dummy.matrix);
            }
            this._inst.instanceMatrix.needsUpdate = true;
        } else if (!this.useWebGL) {
            this._populate2D();
        }
    }

    resetCamera() {
        if (this.useWebGL && this.die) {
            const dieW = this.die.x2 - this.die.x1;
            const dieH = this.die.y2 - this.die.y1;
            const maxDim = Math.max(dieW, dieH);
            const cx = (this.die.x1 + this.die.x2) / 2;
            const cy = (this.die.y1 + this.die.y2) / 2;
            this.camera.position.set(0, -maxDim * 1.1, maxDim * 0.7);
            this.controls.target.set(cx, cy, 0);
            this.controls.update();
        } else if (!this.useWebGL) {
            this._cameraYaw = -0.6;
            this._cameraPitch = 0.9;
            this._cameraZoom = 1.0;
            this._populate2D();
        }
    }

    _resize() {
        if (!this.container || !this.renderer) return;
        const w = this.container.clientWidth;
        const h = this.container.clientHeight;
        if (w === 0 || h === 0) return;
        this.renderer.setSize(w, h);
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
    }

    _start() {
        const tick = () => {
            this._raf = requestAnimationFrame(tick);
            this.controls.update();
            this.renderer.render(this.scene, this.camera);
        };
        tick();
    }

    dispose() {
        if (this._raf) cancelAnimationFrame(this._raf);
        if (this._ro) this._ro.disconnect();
        if (this._ro2d) this._ro2d.disconnect();
        if (this.renderer) {
            this.renderer.dispose();
        }
        const c = this.container && this.container.querySelector('canvas');
        if (c) c.remove();
    }
}

// ===== Mode toggle (Layout / Height / Reset) =====
document.querySelectorAll('#viz3dControls .viz3d-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const mode = btn.dataset.mode;
        if (mode === 'reset') {
            __viz3d.resetCameras();
            return;
        }
        document.querySelectorAll('#viz3dControls .viz3d-btn').forEach(b => {
            if (b.dataset.mode !== 'reset') b.classList.remove('active');
        });
        btn.classList.add('active');
        __viz3d.setMode(mode);
    });
});

function visualize(components, die, name) {
    // Legacy 2D path — replaced by 3D viewer. Kept as a no-op so
    // existing callers don't break.
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
