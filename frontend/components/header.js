document.addEventListener('DOMContentLoaded', () => {
  const header = document.createElement('header');
  const nav = document.createElement('nav');

  const home = document.createElement('a');
  home.href = 'index.html';
  home.textContent = 'Home';
  nav.appendChild(home);

  const profile = document.createElement('a');
  profile.href = 'profile.html';
  profile.textContent = 'Profile';
  nav.appendChild(profile);

  header.appendChild(nav);
  document.body.prepend(header);
});
