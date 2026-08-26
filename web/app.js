// ChipPlacer frontend — multi-objective display
let currentFile = null;
let currentResults = null;

const ALGO_COLORS = {
    'random': '#a0aec0',
    'sa': '#3182ce',
    'ga': '#38a169',
    'eplace': '#d69e2e',
    'gat': '#e53e3e',
};

const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const fileName = document.getElementById('fileName');
const runBtn = document.getElementById('runBtn');
const loading = document.getElementById('loading');
const loadingText = document.getElementById('loadingText');
const resultsSection = document.getElementById('resultsSection');
const exampleLink = document.getElementById('loadExample');

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) setFile(e.target.files[0]);
});

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragging');
});
uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragging'));
uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragging');
    if (e.dataTransfer.files.length > 0) setFile(e.dataTransfer.files[0]);
});

function setFile(file) {
    if (!file.name.endsWith('.def')) {
        alert('Please upload a .def file');
        return;
    }
    currentFile = file;
    fileName.textContent = `✓ ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    runBtn.disabled = false;
}

function loadExample(filename, displayName) {
    return async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`/static/examples/${filename}`);
            if (!response.ok) throw new Error(`Could not load ${filename}`);
            const blob = await response.blob();
            const file = new File([blob], filename, { type: 'text/plain' });
            setFile(file);
            showStatus(`Loaded example: ${displayName} (${(file.size / 1024).toFixed(0)} KB). Click "Run comparison" to see results.`, 'info');
        } catch (err) {
            alert('Could not load example: ' + err.message);
        }
    };
}

exampleLink.addEventListener('click', loadExample('gcd_734cells.def', 'GCD (734 cells)'));

const example5k = document.getElementById('loadExample5k');
if (example5k) example5k.addEventListener('click', loadExample('bigblue1_5k_subset.def', '5K bigblue1 subset (5,000 cells)'));

const example8k = document.getElementById('loadExample8k');
if (example8k) example8k.addEventListener('click', loadExample('bigblue1_8k_subset.def', '8K bigblue1 subset (8,000 cells)'));

const example15k = document.getElementById('loadExample15k');
if (example15k) example15k.addEventListener('click', loadExample('bigblue1_15k_subset.def', '15K bigblue1 subset (15,000 cells)'));

runBtn.addEventListener('click', async () => {
    if (!currentFile) return;

    const selectedAlgos = Array.from(document.querySelectorAll('.algo-card input:checked'))
        .map(cb => cb.value);
    if (selectedAlgos.length === 0) {
        alert('Please select at least one algorithm');
        return;
    }

    runBtn.disabled = true;
    loading.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    loadingText.textContent = `Running ${selectedAlgos.length} algorithms + predicting 5 metrics...`;

    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('algorithms', selectedAlgos.join(','));

    try {
        const response = await fetch('/api/compare', {
            method: 'POST',
            body: formData,
        });
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Server error');
        }
        currentResults = await response.json();
        displayResults(currentResults);
    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        runBtn.disabled = false;
        loading.classList.add('hidden');
    }
});

function fmt(n) {
    if (n === null || n === undefined) return '—';
    if (n >= 1e6) return (n / 1e6).toFixed(2) + 'M';
    if (n >= 1e3) return (n / 1e3).toFixed(2) + 'K';
    if (n < 10) return n.toFixed(2);
    return Math.round(n).toLocaleString();
}

function displayResults(data) {
    resultsSection.classList.remove('hidden');
    document.getElementById('chipInfo').textContent =
        `${data.n_cells} cells, ${data.n_nets} nets`;

    const tbody = document.getElementById('resultsTableBody');
    tbody.innerHTML = '';

    data.results.forEach((result, idx) => {
        if (result.error) {
            const row = tbody.insertRow();
            row.innerHTML = `<td>${result.algorithm}</td><td colspan="6" style="color:#e53e3e">Error: ${result.error}</td>`;
            return;
        }
        const row = tbody.insertRow();
        if (idx === 0) row.classList.add('winner');
        const m = result.metrics || {};
        row.innerHTML = `
            <td><strong>${result.algorithm}</strong>${result.note ? ` <small style="color:#dd6b20">${result.note}</small>` : ''}</td>
            <td>${fmt(result.hpwl)}</td>
            <td>${fmt(m.timing_ps)}</td>
            <td>${fmt(m.power_mw)}</td>
            <td>${fmt(m.area)}</td>
            <td>${fmt(m.max_congestion)}</td>
            <td>${result.time.toFixed(2)}s</td>
        `;
    });

    const vizAlgo = document.getElementById('vizAlgo');
    vizAlgo.innerHTML = '';
    data.results.filter(r => !r.error && r.components).forEach(result => {
        const opt = document.createElement('option');
        opt.value = result.algo_id;
        opt.textContent = result.algorithm;
        vizAlgo.appendChild(opt);
    });

    vizAlgo.addEventListener('change', () => visualize(vizAlgo.value));
    if (data.results.length > 0 && !data.results[0].error) {
        vizAlgo.value = data.results[0].algo_id;
        visualize(data.results[0].algo_id);
    }

    // Compute savings vs. industry baseline
    const winner = data.results.find(r => !r.error);
    if (winner) {
        computeSavings(winner.hpwl);
    }

    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

async function computeSavings(hpwl) {
    try {
        const response = await fetch(`/api/savings?hpwl=${hpwl}`);
        if (!response.ok) return;
        const s = await response.json();

        document.getElementById('savingsCost').textContent =
            `$${(s.tool_cost_saved_usd_per_year / 1000000).toFixed(1)}M`;
        document.getElementById('savingsEnergy').textContent =
            `${s.energy_saved_gwh_per_year.toFixed(1)} GWh`;
        document.getElementById('savingsHeat').textContent =
            `${(s.heat_saved_btu_hr_at_1B_chips / 1000000).toFixed(1)}M BTU/hr`;
        document.getElementById('savingsPower').textContent =
            `${s.power_saved_pct.toFixed(1)}%`;

        document.getElementById('savingsSection').classList.remove('hidden');
    } catch (err) {
        // ignore
    }
}

function visualize(algoId) {
    if (!currentResults) return;
    const result = currentResults.results.find(r => r.algo_id === algoId);
    if (!result || !result.components) return;

    const canvas = document.getElementById('placementCanvas');
    const ctx = canvas.getContext('2d');
    const die = currentResults.die;

    const width = canvas.width;
    const height = canvas.height;
    const padding = 20;
    const drawW = width - 2 * padding;
    const drawH = height - 2 * padding;
    const dieW = die.x2 - die.x1;
    const dieH = die.y2 - die.y1;
    const scale = Math.min(drawW / dieW, drawH / dieH);

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#fafafa';
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = '#cbd5e0';
    ctx.lineWidth = 1;
    ctx.strokeRect(padding, padding, dieW * scale, dieH * scale);

    const color = ALGO_COLORS[algoId] || '#4a5568';
    ctx.fillStyle = color;
    ctx.globalAlpha = 0.6;
    const cellNames = Object.keys(result.components);
    cellNames.forEach(name => {
        const pos = result.components[name];
        const cx = padding + (pos.x - die.x1) * scale;
        const cy = padding + (pos.y - die.y1) * scale;
        ctx.beginPath();
        ctx.arc(cx, cy, 3, 0, Math.PI * 2);
        ctx.fill();
    });
    ctx.globalAlpha = 1.0;
    ctx.fillStyle = '#2d3748';
    ctx.font = '12px sans-serif';
    const m = result.metrics || {};
    ctx.fillText(`${result.algorithm} — ${fmt(result.hpwl)} HPWL — ${fmt(m.timing_ps)}ps — ${fmt(m.power_mw)}mW — ${fmt(m.area)} area — ${fmt(m.max_congestion)} cong`, padding, height - 8);
}
