(() => {
  // Mobile navigation repair. The base stylesheet's <=640px rule places the
  // side-nav at inset: 0, which makes it permanently cover the dashboard.
  const navToggle = document.getElementById('nav-toggle');
  const sideNav = document.querySelector('.side-nav');

  if (navToggle && sideNav) {
    const mobileNavStyle = document.createElement('style');
    mobileNavStyle.id = 'lifehub-mobile-nav-fix';
    mobileNavStyle.textContent = `
      @media (max-width: 900px) {
        body .side-nav {
          position: fixed;
          inset: 0 auto 0 0;
          width: min(82vw, 320px);
          height: 100dvh;
          max-height: 100dvh;
          padding: 4.75rem 0.9rem 1.25rem;
          border-radius: 0 1rem 1rem 0;
          overflow-y: auto;
          overscroll-behavior: contain;
          transform: translateX(-105%);
          transition: transform 180ms ease, visibility 180ms ease;
          visibility: hidden;
          pointer-events: none;
          z-index: 1000;
          box-sizing: border-box;
        }

        body .side-nav.mobile-open {
          inset: 0 auto 0 0;
          transform: translateX(0);
          visibility: visible;
          pointer-events: auto;
        }

        body.nav-open .side-nav {
          inset: 0 auto 0 0;
        }

        #nav-toggle.nav-toggle {
          display: grid !important;
          place-items: center;
          position: fixed;
          top: max(0.85rem, env(safe-area-inset-top));
          left: max(0.85rem, env(safe-area-inset-left));
          width: 3rem;
          height: 3rem;
          padding: 0;
          z-index: 1002;
          font-size: 1.65rem;
          line-height: 1;
          color: var(--color-text);
          background: var(--color-card);
          border: 1px solid var(--color-border);
          border-radius: 0.9rem;
          box-shadow: var(--shadow-panel);
        }

        #nav-toggle.nav-toggle[aria-expanded="true"] {
          background: var(--surface-strong);
        }

        .mobile-nav-backdrop {
          position: fixed;
          inset: 0;
          z-index: 999;
          border: 0;
          padding: 0;
          background: rgba(3, 8, 20, 0.64);
          backdrop-filter: blur(2px);
          opacity: 0;
          visibility: hidden;
          pointer-events: none;
          transition: opacity 180ms ease, visibility 180ms ease;
        }

        body.nav-open .mobile-nav-backdrop {
          opacity: 1;
          visibility: visible;
          pointer-events: auto;
        }

        body.nav-open {
          overflow: hidden;
        }

        .side-nav-title {
          padding-right: 2.5rem;
        }

        .side-nav a {
          min-height: 44px;
          display: flex;
          align-items: center;
        }
      }

      @media (prefers-reduced-motion: reduce) {
        body .side-nav,
        .mobile-nav-backdrop {
          transition: none !important;
        }
      }
    `;
    document.head.appendChild(mobileNavStyle);

    const backdrop = document.createElement('button');
    backdrop.type = 'button';
    backdrop.className = 'mobile-nav-backdrop';
    backdrop.setAttribute('aria-label', 'Close navigation');
    document.body.insertBefore(backdrop, document.body.firstChild);

    const isMobile = () => window.matchMedia('(max-width: 900px)').matches;

    const setNavOpen = (open) => {
      const next = Boolean(open && isMobile());
      sideNav.classList.toggle('mobile-open', next);
      document.body.classList.toggle('nav-open', next);
      navToggle.setAttribute('aria-expanded', String(next));
      navToggle.setAttribute('aria-label', next ? 'Close navigation' : 'Open navigation');
      navToggle.textContent = next ? '×' : '☰';
    };

    navToggle.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      setNavOpen(navToggle.getAttribute('aria-expanded') !== 'true');
    });

    backdrop.addEventListener('click', () => setNavOpen(false));

    sideNav.addEventListener('click', (event) => {
      if (event.target.closest('a')) setNavOpen(false);
    });

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') setNavOpen(false);
    });

    window.addEventListener('resize', () => {
      if (!isMobile()) setNavOpen(false);
    });

    setNavOpen(false);
  }

  // Shared podcast launcher and its Dashboard settings integration.
  if (document.querySelector('script[data-josh-podcast-dock="true"]')) return;

  const script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/gh/joshualparris/JoshHub@ebb0d17495c92d3ce09df1fd1bdb5d4c2056914d/public/podcast-launcher-v3.js';
  script.defer = true;
  script.dataset.joshPodcastDock = 'true';
  script.dataset.topics = 'it,software,research,faith,relationships,career,decision,homelab,horses';
  script.dataset.defaultTopic = 'faith';
  script.dataset.launcherLabel = '🎧 Podcasts';
  script.dataset.settingsTarget = '.settings-sheet';

  const mountPodcastSetting = () => {
    const settingsHost = document.querySelector('.settings-sheet');
    if (settingsHost && window.JoshPodcastDock) {
      window.JoshPodcastDock.mountSettings();
      return true;
    }
    return false;
  };

  script.addEventListener('load', () => {
    if (mountPodcastSetting()) return;
    const observer = new MutationObserver(() => {
      if (mountPodcastSetting()) observer.disconnect();
    });
    observer.observe(document.body, { childList: true, subtree: true });
  });

  document.body.appendChild(script);
})();