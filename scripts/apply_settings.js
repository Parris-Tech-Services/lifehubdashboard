// Read dashboard visibility settings from localStorage and apply them to the page.
(function () {
  const KEY = 'lh_dashboard_visibility';

  function read() {
    try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; }
  }

  function apply(settings) {
    // for each key, find element by id and hide/show
    Object.keys(settings || {}).forEach(id => {
      const el = document.getElementById(id);
      if (!el) return;
      const visible = !!settings[id];
      if (!visible) {
        el.classList.add('hidden-by-settings');
        el.setAttribute('aria-hidden', 'true');
      } else {
        el.classList.remove('hidden-by-settings');
        el.removeAttribute('aria-hidden');
      }
    });
  }

  // Expose a function so the settings page can call it when opened as a popup
  window.applyDashboardVisibility = function (settings) {
    // merge with existing so unspecified keys are left alone
    const current = read();
    const merged = Object.assign({}, current, settings);
    localStorage.setItem(KEY, JSON.stringify(merged));
    apply(merged);
  };

  document.addEventListener('DOMContentLoaded', () => {
    try { apply(read()); } catch (e) { /* ignore on malformed storage */ }
  });

  // Listen for storage events from other tabs (sync)
  window.addEventListener('storage', (ev) => {
    if (ev.key === KEY) {
      try { apply(JSON.parse(ev.newValue || '{}')); } catch (e) { /* ignore */ }
    }
  });

  // Listen for BroadcastChannel messages (works across tabs and is more reliable for file: origin in some browsers)
  try {
    if (typeof BroadcastChannel !== 'undefined') {
      const ch = new BroadcastChannel('lh_settings');
      ch.addEventListener('message', (ev) => {
        try { apply(ev.data || {}); } catch (e) { /* ignore malformed */ }
      });
    }
  } catch (e) { /* ignore */ }

  // Wire the Settings button if present
  document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('open-settings');
    if (!btn) return;
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      // open settings in a new tab/window
      const w = window.open('settings.html', '_blank');
      if (w) w.focus();
    });
  });
})();
