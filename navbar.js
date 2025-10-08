document.addEventListener('DOMContentLoaded', async () => {
  const navbarContainer = document.getElementById('navbar-container');

  // Load navbar HTML
  const response = await fetch('/navbar.html');
  const navbarHTML = await response.text();
  navbarContainer.innerHTML = navbarHTML;

  const usernameSpan = document.getElementById('username');
  const token = localStorage.getItem('jwt');

  if (!token) {
    usernameSpan.innerHTML = 'Guest (<a href="/login.html" class="text-pink-600 hover:underline">Login</a>)';
    return;
  }

  try {
    const res = await fetch('https://api.kingburger.site/dashboard', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!res.ok) throw new Error('Unauthorized');

    const data = await res.json();
    usernameSpan.innerHTML = data.loggedIn_User;

    // Optional: refresh token
    if (data.token) localStorage.setItem('jwt', data.token);
  } catch (err) {
    console.log('User not logged in or token expired', err);
    usernameSpan.innerHTML = 'Guest (<a href="/login.html" class="text-pink-600 hover:underline">Login</a>)';
  }
});
