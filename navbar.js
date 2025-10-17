document.addEventListener('DOMContentLoaded', async () => {
  const navbarContainer = document.getElementById('navbar-container');
  if (!navbarContainer) return;

  try {
    const response = await fetch('/navbar.html');
    if (!response.ok) throw new Error('Failed to load navbar');
    navbarContainer.innerHTML = await response.text();

    const usernameSpan = document.getElementById('username');
    const profileLink = document.getElementById('profileLink');
    const logoutLink = document.getElementById('logoutLink');
    const token = localStorage.getItem('jwt');

    if (!token) {
      showGuest(usernameSpan, profileLink, logoutLink);
      return;
    }

    if (profileLink) profileLink.style.display = 'inline';
    if (logoutLink) logoutLink.style.display = 'inline';

    try {
      const res = await fetch('https://api.kingburger.site/dashboard', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!res.ok) throw new Error('Unauthorized');

      const data = await res.json();
      usernameSpan.innerText = `Logged in User: ${data.loggedIn_User || 'User'}`;
    } catch (err) {
      console.warn('Token invalid or user not logged in', err);
      showGuest(usernameSpan, profileLink, logoutLink);
    }

    if (logoutLink) {
      logoutLink.addEventListener('click', () => {
        if (confirm("Are you sure you want to log out?")) {
          localStorage.removeItem('jwt');
          window.location.href = '/index.html';
        }
      });
    }

  } catch (err) {
    console.error('Navbar failed to load:', err);
  }
});

// Helper function to show Guest
function showGuest(usernameSpan, profileLink, logoutLink) {
  usernameSpan.innerHTML = '<span class="text-white">Guest</span> (<a href="/login.html" class="text-pink-600 hover:underline">Login</a>)';
  if (profileLink) profileLink.style.display = 'none';
  if (logoutLink) logoutLink.style.display = 'none';
}

// Reusable function to require login
export function reqLogin() {
  const token = localStorage.getItem('jwt');
  if (!token) {
    window.location.href = '/redirects/401.html';
  }
}
