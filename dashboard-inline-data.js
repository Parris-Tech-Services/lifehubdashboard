(() => {
  if (document.querySelector('script[data-josh-podcast-dock="true"]')) return;

  const script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/gh/joshualparris/JoshHub@7b6ec3907b27924dbe1d64c9ece4e439e6de8de7/public/podcast-dock.js';
  script.defer = true;
  script.dataset.joshPodcastDock = 'true';
  script.dataset.topics = 'it,software,research,faith,relationships,career,decision,homelab,horses';
  script.dataset.defaultTopic = 'faith';

  const mountPodcastSetting = () => {
    const settingsHost = document.querySelector('.settings-sheet');
    if (settingsHost && window.JoshPodcastDock) {
      window.JoshPodcastDock.mountSettings(settingsHost);
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
