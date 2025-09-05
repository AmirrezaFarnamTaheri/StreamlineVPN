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
(function () {
  const blocks = document.querySelectorAll('pre');
  blocks.forEach(pre => {
    if (pre.querySelector('.copy-btn')) return;
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.type = 'button';
    btn.textContent = 'Copy';
    btn.addEventListener('click', async () => {
      const text = pre.innerText;
      try {
        await navigator.clipboard.writeText(text);
        btn.textContent = 'Copied!';
        setTimeout(() => (btn.textContent = 'Copy'), 1200);
      } catch (_) {
        const range = document.createRange();
        range.selectNodeContents(pre);
        const sel = window.getSelection();
        sel.removeAllRanges(); sel.addRange(range);
        btn.textContent = 'Selected';
        setTimeout(() => (btn.textContent = 'Copy'), 1200);
      }
    });
    pre.appendChild(btn);
  });
})();

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
