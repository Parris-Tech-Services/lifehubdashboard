// Simple settings UI for dashboard section visibility
(function () {
  // Default known sections (fallback). We prefer to detect panels from the opener dashboard when available.
  const DEFAULT_SECTIONS = [
    { selector: '#wellbeing-widget', label: 'Wellbeing snapshot' },
    { selector: '#inbox-health-panel', label: 'Inbox health' },
    { selector: '#today-panel', label: 'Today / Agenda' },
    { selector: '#automation-scheduler-panel', label: 'Automation scheduler' },
    { selector: '#timeline-panel', label: 'Activity timeline' },
    { selector: '#recent-files-panel', label: 'Recent files' },
    { selector: '#backup-panel', label: 'Backup integrity' },
    { selector: '#downloads-panel', label: 'Downloads watcher' },
    { selector: '#resurface-panel', label: 'Resurface carousel' },
    { selector: '#scratchpad-panel', label: 'Project scratchpad' },
    { selector: '#playables', label: 'Playable projects' },
    { selector: '#triage-panel', label: 'Inbox triage board' },
    { selector: '#copilot-panel', label: 'Copilot' },
    { selector: '#card-grid', label: 'Card grid' },
    { selector: '.checklist', label: 'Weekly checklist' },
    { selector: '#resource-spotlight', label: 'Resource spotlight' },
    { selector: '.utility', label: 'Utility strip (search + quick actions)' },
    { selector: 'header', label: 'Header' },
    { selector: 'footer', label: 'Footer' }
  ];

  const KEY = 'lh_dashboard_visibility';

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; }
  }
  function save(obj) { localStorage.setItem(KEY, JSON.stringify(obj)); }
  function applyToPage(settings) {
    // Try to notify the opener (if the settings page was opened from the dashboard)
    try {
      if (window.opener && typeof window.opener.applyDashboardVisibility === 'function') {
        window.opener.applyDashboardVisibility(settings);
      }
    } catch (e) { /* ignore cross-origin or other errors */ }
    // Persist to localStorage and broadcast via BroadcastChannel for broader sync (helps when file:// has limited storage events)
    save(settings);
    try {
      if (typeof BroadcastChannel !== 'undefined') {
        const ch = new BroadcastChannel('lh_settings');
        ch.postMessage(settings);
        ch.close();
      }
    } catch (e) { /* ignore */ }
    // Also attempt to call a generic setter on the opener if available (for broader compatibility)
    try {
      if (window.opener && typeof window.opener.applyDashboardVisibility === 'function') {
        window.opener.applyDashboardVisibility(settings);
      } else if (window.opener && window.opener.postMessage) {
        // Post a message to opener so it can optionally apply settings if it listens
        window.opener.postMessage({ type: 'lh_settings', settings }, '*');
      }
    } catch (e) { /* ignore cross-origin or other errors */ }
  }

  // Build list of toggles from sections array where each item has { selector, label }
  function buildList(container, settings, sections) {
    container.innerHTML = '';
    sections.forEach(s => {
      const key = s.selector;
      const div = document.createElement('div'); div.className = 'setting-item';
      const label = document.createElement('label'); label.textContent = s.label || s.selector;
      const cb = document.createElement('input'); cb.type = 'checkbox'; cb.dataset.selector = key;
      cb.checked = settings[key] !== undefined ? !!settings[key] : true;
      const left = document.createElement('div'); left.style.display = 'flex'; left.style.flexDirection = 'column'; left.appendChild(label);
      const right = document.createElement('div'); right.appendChild(cb);
      div.appendChild(left); div.appendChild(right);
      container.appendChild(div);
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    const list = document.getElementById('settings-list');
    const saveBtn = document.getElementById('settings-save');
    const resetBtn = document.getElementById('settings-reset');
    const current = load();
    // Try to detect panels from the dashboard opener to show everything the user can hide
    (async function populate() {
      let sections = DEFAULT_SECTIONS.slice();
      try {
        if (window.opener && window.opener.document) {
          // collect panels and elements with ids from the opener
          const docs = window.opener.document;
          const found = [];
          // prefer sections and elements with class 'panel' or with id attributes
          const panels = Array.from(docs.querySelectorAll('section.panel, .panel, [id]'));
          panels.forEach(el => {
            const sel = el.id ? `#${el.id}` : computeUniqueSelector(el);
            const label = el.getAttribute('data-panel-label') || el.id || el.className || el.tagName.toLowerCase();
            // avoid duplicates
            if (!found.some(f => f.selector === sel)) found.push({ selector: sel, label: label });
          });
          if (found.length) sections = found.concat(sections.filter(d => !found.some(f => f.selector === d.selector)));
        }
      } catch (e) {
        // cross-origin or file:// restrictions — fall back to defaults
      }
      buildList(list, current, sections);
    })();

    saveBtn.addEventListener('click', () => {
      const nodes = Array.from(list.querySelectorAll('input[type=checkbox]'));
      const obj = {};
      nodes.forEach(n => { obj[n.dataset.selector] = !!n.checked; });
      applyToPage(obj);
      alert('Settings saved — they will apply to any open dashboard tabs.');
    });

    resetBtn.addEventListener('click', () => {
      if (!confirm('Reset dashboard visibility to defaults (show all)?')) return;
      const nodes = Array.from(list.querySelectorAll('input[type=checkbox]'));
      const obj = {};
      nodes.forEach(n => { obj[n.dataset.selector] = true; });
      buildList(list, obj, Array.from(list.querySelectorAll('.setting-item')).map(() => { /* keep existing DOM items */ }));
      applyToPage(obj);
      alert('Settings reset.');
    });
  });

  // Helper to compute a simple selector fallback for elements without an id
  function computeUniqueSelector(el) {
    try {
      const parts = [];
      let cur = el;
      while (cur && cur.nodeType === 1 && parts.length < 5) {
        let part = cur.tagName.toLowerCase();
        if (cur.className) {
          const cls = String(cur.className).trim().split(/\s+/)[0];
          if (cls) part += `.${cls}`;
        }
        parts.unshift(part);
        cur = cur.parentElement;
      }
      return parts.length ? parts.join(' > ') : el.tagName.toLowerCase();
    } catch (e) { return el.id ? `#${el.id}` : el.tagName.toLowerCase(); }
  }
})();
