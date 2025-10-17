document.addEventListener('DOMContentLoaded', async () => {
  const navbarContainer = document.getElementById('navbar-container');
  if (!navbarContainer) return;

  // Load navbar HTML
  try {
    const response = await fetch('/navbar.html');
    if (!response.ok) throw new Error('Failed to load navbar');
    navbarContainer.innerHTML = await response.text();

    // DOM elements
    const usernameSpan = document.getElementById('username');
    const profileLink = document.getElementById('profileLink');
    const logoutLink = document.getElementById('logoutLink');
    const token = localStorage.getItem('jwt');

    // User is not logged in
    if (!token) {
      usernameSpan.innerHTML = '<span class="text-white">Guest</span> (<a href="/login.html" class="text-pink-600 hover:underline">Login</a>)';
      if (profileLink) profileLink.style.display = 'none';
      if (logoutLink) logoutLink.style.display = 'none';
      return;
    }

    // Show profile/logout links for logged-in users
    if (profileLink) profileLink.style.display = 'inline';
    if (logoutLink) logoutLink.style.display = 'inline';

    // Fetch user info
    try {
      const res = await fetch('https://api.kingburger.site/dashboard', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!res.ok) throw new Error('Unauthorized');

      const data = await res.json();
      usernameSpan.innerText = `Logged in User: ${data.loggedIn_User || 'User'}`;

    } catch (err) {
      console.warn('Token invalid or user not logged in', err);
      usernameSpan.innerHTML = 'Guest (<a href="/login.html" class="text-pink-600 hover:underline">Login</a>)';
      if (profileLink) profileLink.style.display = 'none';
      if (logoutLink) logoutLink.style.display = 'none';
    }

    // Logout functionality
    if (logoutLink) {
      logoutLink.addEventListener('click', () => {
        if (confirm("Are you sure you want to log out?")) {
          localStorage.removeItem('jwt');
          window.location.href = '/login.html';
        }
      });
    }

  } catch (err) {
    console.error('Navbar failed to load:', err);
  }
});

export function reqLogin(token) {
  if (!token) {
    window.location.href = '/401.html';
  }
}
