// API Configuration
const API_BASE = (() => {
    // Prefer value injected by the static server if present
    const injected = window.__API_BASE__;
    if (typeof injected === 'string' && injected.startsWith('http')) return injected;
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return `http://${hostname}:8080`;
    }
    return `${window.location.protocol}//${window.location.host}`;
})();

console.log('API Base:', API_BASE);

// Global state
let chart = null;
let currentTab = 'dashboard';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    loadStatistics();
    setInterval(loadStatistics, 5000);
});

// Tab switching
const tablist = document.getElementById('tablist');
const tabContents = document.querySelectorAll('.tab-content');
const tabs = tablist.querySelectorAll('.tab-btn');

function switchTab(targetTab) {
    tabContents.forEach(content => {
        const isTarget = content.id === `${targetTab}-tab`;
        content.classList.toggle('active', isTarget);
        content.toggleAttribute('hidden', !isTarget);
    });

    tabs.forEach(tab => {
        const isTarget = tab.dataset.tab === targetTab;
        tab.setAttribute('aria-selected', isTarget);
        tab.setAttribute('tabindex', isTarget ? '0' : '-1');
    });

    currentTab = targetTab;
    if (targetTab === 'configs') loadConfigurations();
    if (targetTab === 'sources') loadSources();
}

tablist.addEventListener('click', (e) => {
    const tabButton = e.target.closest('.tab-btn');
    if (tabButton) {
        switchTab(tabButton.dataset.tab);
    }
});

tablist.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        e.preventDefault();
        const currentTabIndex = Array.from(tabs).indexOf(e.target);
        const nextTabIndex = e.key === 'ArrowRight'
            ? (currentTabIndex + 1) % tabs.length
            : (currentTabIndex - 1 + tabs.length) % tabs.length;
        tabs[nextTabIndex].focus();
        switchTab(tabs[nextTabIndex].dataset.tab);
    }
});

// Set initial tab
switchTab('dashboard');

// Initialize chart
function initChart() {
    const ctx = document.getElementById('chart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Configurations',
                data: [],
                borderColor: 'rgba(94, 80, 249, 1)',
                backgroundColor: 'rgba(94, 80, 249, 0.2)',
                tension: 0.4,
                fill: true,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: 'rgba(248, 249, 250, 1)' }
                }
            },
            scales: {
                x: {
                    ticks: { color: 'rgba(160, 174, 192, 1)' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                },
                y: {
                    ticks: { color: 'rgba(160, 174, 192, 1)' },
                    grid: { color: 'rgba(255, 255, 255, 0.05)' }
                }
            }
        }
    });
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/statistics`);
        const contentType = response.headers.get('content-type') || '';
        if (!response.ok || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`HTTP ${response.status}: ${text.substring(0, 100)}`);
        }
        const stats = await response.json();

        document.getElementById('totalConfigs').textContent = stats.total_configs || 0;
        document.getElementById('activeSources').textContent = stats.total_sources || 0;
        document.getElementById('successRate').textContent = Math.round((stats.success_rate || 0) * 100) + '%';
        document.getElementById('avgQuality').textContent = (stats.avg_quality || 0).toFixed(2);

        // Update chart
        if (chart) {
            const time = new Date().toLocaleTimeString();
            chart.data.labels.push(time);
            chart.data.datasets[0].data.push(stats.total_configs || 0);

            if (chart.data.labels.length > 10) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }

            chart.update();
        }
    } catch (error) {
        console.error('Failed to load statistics:', error);
    }
}

// Load configurations
async function loadConfigurations() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/configurations?limit=50`);
        const data = await response.json();
        const container = document.getElementById('configsList');
        container.innerHTML = '';

        if (data.configurations && data.configurations.length > 0) {
            data.configurations.forEach(config => {
                const div = document.createElement('div');
                div.className = 'glass p-4 flex flex-col justify-between';
                div.innerHTML = `
                    <div>
                        <div class="font-bold text-light">${config.protocol.toUpperCase()}</div>
                        <div class="text-sm text-gray">${config.server}:${config.port}</div>
                    </div>
                    <div class="text-right text-success font-semibold">${(config.quality_score * 100).toFixed(0)}%</div>
                `;
                container.appendChild(div);
            });
        } else {
            container.innerHTML = '<div class="text-center text-gray col-span-full">No configurations available</div>';
        }
    } catch (error) {
        console.error('Failed to load configurations:', error);
        document.getElementById('configsList').innerHTML = '<div class="text-center text-danger col-span-full">Failed to load configurations.</div>';
    }
}

// Load sources
async function loadSources() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/sources`);
        const data = await response.json();
        const container = document.getElementById('sourcesList');
        container.innerHTML = '';

        if (data.sources && data.sources.length > 0) {
            data.sources.forEach(source => {
                let displayName = source.url || '';
                try {
                    const u = new URL(displayName);
                    displayName = u.hostname;
                } catch (e) { /* use as is */ }

                const successRate = typeof source.success_rate === 'number' ? (source.success_rate * 100).toFixed(0) : 'N/A';
                const configs = source.configs ?? source.avg_config_count ?? 0;

                const div = document.createElement('div');
                div.className = 'glass p-4 flex justify-between items-center';
                div.innerHTML = `
                    <div>
                        <div class="font-semibold text-light">${displayName}</div>
                        <div class="text-sm text-gray">Configs: ${configs} | Success: ${successRate}%</div>
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="status-dot ${source.status === 'active' ? 'status-active' : 'status-inactive'}"></span>
                        <span class="text-sm capitalize">${source.status}</span>
                    </div>
                `;
                container.appendChild(div);
            });
        } else {
            container.innerHTML = '<div class="text-center text-gray">No sources configured</div>';
        }
    } catch (error) {
        console.error('Failed to load sources:', error);
        document.getElementById('sourcesList').innerHTML = '<div class="text-center text-danger">Failed to load sources.</div>';
    }
}

// Start processing
document.getElementById('startProcessingBtn').addEventListener('click', async () => {
    const configPath = document.getElementById('configPath').value;
    const formats = Array.from(document.querySelectorAll('.format-cb:checked')).map(cb => cb.value);

    if (formats.length === 0) {
        alert('Please select at least one output format');
        return;
    }

    const startBtn = document.getElementById('startProcessingBtn');
    const prevText = startBtn.textContent;
    startBtn.disabled = true;
    startBtn.textContent = 'Processing...';

    document.getElementById('progressBar').classList.remove('hidden');
    updateProgress(0, 'Starting...');

    try {
        const response = await fetch(`${API_BASE}/api/v1/pipeline/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                config_path: configPath,
                output_dir: 'output',
                formats: formats
            })
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const result = await response.json();

        if (result.job_id) {
            monitorJob(result.job_id, () => {
                loadStatistics();
                loadConfigurations();
                startBtn.disabled = false;
                startBtn.textContent = prevText;
            }, (errMsg) => {
                startBtn.disabled = false;
                startBtn.textContent = prevText;
            });
        } else {
            throw new Error(result.message || 'Failed to start processing');
        }
    } catch (error) {
        console.error('Processing error:', error);
        addTerminalLine(`Error: ${error.message}`, 'error');
        updateProgress(0, 'Failed');
        startBtn.disabled = false;
        startBtn.textContent = prevText;
    }
});

// Monitor job progress
async function monitorJob(jobId, onComplete, onFail) {
    const checkInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/v1/pipeline/status/${jobId}`);
            const contentType = response.headers.get('content-type') || '';
            if (!response.ok || !contentType.includes('application/json')) {
                const text = await response.text();
                throw new Error(`HTTP ${response.status}: ${text.substring(0, 100)}`);
            }
            const status = await response.json();

            updateProgress(status.progress || 0, status.message || 'Processing...');
            addTerminalLine(`[${jobId.substr(0, 8)}] ${status.message}`);

            if (status.status === 'completed') {
                clearInterval(checkInterval);
                updateProgress(100, 'Completed!');
                addTerminalLine('✅ Processing completed successfully', 'success');
                if (onComplete) onComplete();
            } else if (status.status === 'failed') {
                clearInterval(checkInterval);
                updateProgress(0, 'Failed');
                addTerminalLine(`❌ Processing failed: ${status.error}`, 'error');
                if (onFail) onFail(status.error);
            }
        } catch (error) {
            clearInterval(checkInterval);
            console.error('Job monitoring error:', error);
            addTerminalLine(`Error: ${error.message}`, 'error');
            if (onFail) onFail(error.message);
        }
    }, 2000);
}

// Update progress bar
function updateProgress(percent, message) {
    document.getElementById('progressFill').style.width = `${percent}%`;
    document.getElementById('progressText').textContent = message;
}

// Add terminal line
function addTerminalLine(text, type = 'info') {
    const terminal = document.getElementById('terminal');
    const line = document.createElement('div');

    const timestamp = new Date().toLocaleTimeString();
    line.textContent = `[${timestamp}] ${text}`;

    if (type === 'error') line.style.color = '#ef4444';
    if (type === 'success') line.style.color = '#10b981';

    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
}
