document.addEventListener('DOMContentLoaded', async () => {
  const usernameSpan = document.getElementById('username');
  const token = localStorage.getItem('jwt');

  if (!usernameSpan) return;

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
    usernameSpan.textContent = data.loggedIn_User || 'Welcome!';

  } catch (err) {
    console.log('User not logged in or token expired', err);
    usernameSpan.innerHTML = 'Guest (<a href="/login.html" class="text-pink-600 hover:underline">Login</a>)';
    localStorage.removeItem('jwt'); // remove invalid token
  }
});
