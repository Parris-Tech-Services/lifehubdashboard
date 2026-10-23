(function () {
  function isPublishedPath(path, paths) {
    return paths.includes(path) || paths.includes(path.replace(/\/$/, '') + '/index.html') || (path === '' && paths.includes('index.html'));
  }
  if (typeof module !== 'undefined') module.exports = { isPublishedPath };
  if (typeof window === 'undefined' || location.protocol === 'file:' || ['localhost', '127.0.0.1'].includes(location.hostname)) return;
  const base = new URL('.', document.currentScript.src);
  document.addEventListener('click', function (event) {
    const anchor = event.target.closest('a[href]');
    if (!anchor || !Array.isArray(window.LIFEHUB_PUBLISHED_PATHS)) return;
    const url = new URL(anchor.href, base);
    if (url.origin !== base.origin || !url.pathname.startsWith(base.pathname) || url.pathname === location.pathname) return;
    let path;
    try { path = decodeURIComponent(url.pathname.slice(base.pathname.length)); } catch { return; }
    if (isPublishedPath(path, window.LIFEHUB_PUBLISHED_PATHS)) return;
    event.preventDefault();
    let notice = document.getElementById('local-file-notice');
    if (!notice) {
      notice = document.createElement('div');
      notice.id = 'local-file-notice';
      notice.setAttribute('role', 'status');
      Object.assign(notice.style, {position:'fixed',bottom:'1rem',left:'1rem',right:'1rem',padding:'1rem',background:'#172635',color:'#fff',border:'2px solid #80c9d9',borderRadius:'12px',zIndex:'10000'});
      const message = document.createElement('p');
      message.textContent = 'This file is in your local LifeHub folders and is not published on this website. Open the dashboard on the computer that stores those folders.';
      const close = document.createElement('button');
      close.textContent = 'Dismiss';
      close.addEventListener('click', () => notice.remove());
      notice.append(message, close);
      document.body.append(notice);
    }
  });
}());
