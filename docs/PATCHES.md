Minimal safe patches (examples)

This file lists low-risk, minimal patches the assistant recommends applying to `LifeHub/dashboard.js` to reduce XSS and unsafe DOM manipulation.

1) Add an escapeHtml helper

function escapeHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

Usage: replace `container.innerHTML = someString` with `container.innerHTML = escapeHtml(someString)` only when `someString` must remain HTML-escaped. Prefer `textContent`.

2) Add a safeSetInnerText helper

function safeSetInnerText(el, str) {
  if (!el) return;
  el.textContent = str == null ? '' : String(str);
}

3) Replace innerHTML list builders with DOM creation helpers

function safeInsertList(container, items, renderItem) {
  container.textContent = '';
  const frag = document.createDocumentFragment();
  for (const it of items) {
    const li = document.createElement('li');
    li.textContent = String(renderItem ? renderItem(it) : it);
    frag.appendChild(li);
  }
  container.appendChild(frag);
}

4) Example replacement (renderRecentFiles)

// old:
// container.innerHTML = files.map(f => `<li>${f.name} — ${f.size}</li>`).join('');
// new:
// safeInsertList(container, files, f => `${f.name} — ${f.size}`);

Notes and caveats

- Some UI areas intentionally accept HTML (rich content). Those should be explicitly documented and sanitized using an allowlist or DOMPurify.
- These patches intentionally minimize risk and changes. A future follow-up should refactor large renderers into small functions and add unit tests.

If you'd like, I can apply these changes directly to `dashboard.js`. Reply with "Apply safe HTML patches" and I'll make the edits and run quick smoke tests.
