(() => {
  if (document.querySelector('script[data-josh-podcast-dock="true"]')) return;

  const script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/gh/joshualparris/JoshHub@35c4348b4adfbc1c64bad8a3d3e31ede008a4441/public/podcast-dock.js';
  script.defer = true;
  script.dataset.joshPodcastDock = 'true';
  script.dataset.topics = 'it,software,research,faith,relationships,career,decision,homelab,horses';
  script.dataset.defaultTopic = 'faith';
  document.body.appendChild(script);
})();
