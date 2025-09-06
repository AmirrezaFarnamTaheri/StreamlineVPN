// Theme toggle across all docs pages
(function () {
  const key = 'slvpn-theme';
  const root = document.documentElement; // apply attribute at root
  const btn = document.getElementById('theme-toggle');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const stored = localStorage.getItem(key);
  const current = stored || (prefersDark ? 'dark' : 'light');
  root.setAttribute('data-theme', current);
  function toggle() {
    const next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    root.setAttribute('data-theme', next);
    localStorage.setItem(key, next);
  }
  if (btn) btn.addEventListener('click', toggle);
})();

// Add copy buttons to code blocks
function addCopyButtons(root = document) {
  const blocks = root.querySelectorAll('pre');
  blocks.forEach(pre => {
    if (pre.querySelector('.copy-btn')) return;
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.type = 'button';
    btn.tabIndex = -1;
    btn.setAttribute('aria-hidden', 'true');
    btn.textContent = 'Copy';
    btn.addEventListener('mousedown', (e) => e.preventDefault());
    btn.addEventListener('click', async () => {
      const target = pre.querySelector('code') || pre;
      const text = target.textContent;
      try {
        await navigator.clipboard.writeText(text);
        btn.textContent = 'Copied!';
        setTimeout(() => (btn.textContent = 'Copy'), 1200);
      } catch (_) {
        const range = document.createRange();
        range.selectNodeContents(target);
        const sel = window.getSelection();
        sel.removeAllRanges(); sel.addRange(range);
        btn.textContent = 'Selected';
        setTimeout(() => {
          btn.textContent = 'Copy';
          sel.removeAllRanges();
        }, 1200);
      }
    });
    pre.appendChild(btn);
  });
}
addCopyButtons();

// Optional homepage health check (only runs if elements exist)
(function () {
  const statusEl = document.getElementById('status');
  const healthLink = document.getElementById('health-link');
  if (!statusEl || !healthLink) return;
  const url = 'http://localhost:8000/health';
  healthLink.addEventListener('click', function(e){ e.preventDefault(); window.open(url, '_blank'); });
  try {
    fetch(url, {mode: 'cors'})
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) {
          statusEl.textContent = `API: ${data.status} • uptime ${Math.round(data.uptime)}s`;
          statusEl.style.color = '#2dd4bf';
        }
      })
      .catch(() => {});
  } catch (e) {}
})();

// Interactive pipeline runner
(function () {
  const form = document.getElementById('pipeline-form');
  const logsEl = document.getElementById('logs');
  const outputFilesEl = document.getElementById('output-files');

  if (!form || !logsEl || !outputFilesEl) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const configPath = form.elements['config-path'].value;
    const outputDir = form.elements['output-dir'].value;
    const formats = [...form.elements['formats']]
      .filter(input => input.checked)
      .map(input => input.value);

    // Clear previous results and revoke URLs
    if (outputFilesEl._objectUrls) {
      outputFilesEl._objectUrls.forEach(u => URL.revokeObjectURL(u));
      delete outputFilesEl._objectUrls;
    }
    logsEl.textContent = 'Running pipeline...';
    outputFilesEl.innerHTML = '<p>Waiting for results...</p>';

    try {
      const response = await fetch('/api/v1/pipeline/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          config_path: configPath,
          output_dir: outputDir,
          formats: formats,
        }),
      });

      const result = await response.json();

      if (response.ok) {
        logsEl.textContent = `Pipeline completed successfully:\n${result.message}`;

        // Revoke any previously created URLs to avoid leaks
        if (outputFilesEl._objectUrls) {
          outputFilesEl._objectUrls.forEach(u => URL.revokeObjectURL(u));
        }
        outputFilesEl.innerHTML = '';
        const objectUrls = [];

        for (const [fileName, content] of Object.entries(result.output_files)) {
          const blob = new Blob([content], { type: 'text/plain' });
          const url = URL.createObjectURL(blob);
          objectUrls.push(url);

          const details = document.createElement('details');
          const summary = document.createElement('summary');
          summary.textContent = fileName;
          details.appendChild(summary);

          const actions = document.createElement('div');
          actions.className = 'output-actions';
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', fileName);
          link.className = 'btn secondary';
          link.textContent = 'Download';
          link.addEventListener('click', () => {
            const href = link.getAttribute('href');
            setTimeout(() => URL.revokeObjectURL(href), 2000);
          }, { once: true });
          actions.appendChild(link);
          details.appendChild(actions);

          const pre = document.createElement('pre');
          pre.textContent = content;
          details.appendChild(pre);

          outputFilesEl.appendChild(details);
        }

        if (!objectUrls.length) {
          outputFilesEl.innerHTML = '<p>No output files produced.</p>';
        }

        outputFilesEl._objectUrls = objectUrls;
        addCopyButtons(outputFilesEl);

      } else {
        logsEl.textContent = `Error:\n${result.detail}`;
      }
    } catch (error) {
      logsEl.textContent = `An unexpected error occurred:\n${error.toString()}`;
    }
  });
})();
