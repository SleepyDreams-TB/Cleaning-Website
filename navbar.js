// navbar.js
document.addEventListener('DOMContentLoaded', async () => {
  const navbarContainer = document.getElementById('navbar-container');
  if (!navbarContainer) return;

  try {
    // Fetch navbar HTML
    const response = await fetch('/navbar.html');
    if (!response.ok) throw new Error('Failed to fetch navbar');
    navbarContainer.innerHTML = await response.text();

    // Grab profile container
    const profileContainer = document.getElementById('profileContainer');
    if (!profileContainer) return;

    const token = localStorage.getItem('jwt');

    if (!token) {
      showGuest(profileContainer);
      return;
    }

    try {
      const res = await fetch('https://api.kingburger.site/users/dashboard/info', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!res.ok) throw new Error('Invalid token');

      const responseData = await res.json();
      showLoggedIn(profileContainer, responseData);

    } catch {
      showGuest(profileContainer);
    }

  } catch (err) {
    console.error('Navbar load failed:', err);
    navbarContainer.innerHTML = `
      <nav class="bg-gray-900 text-white p-4 text-center">
        <a href="/index.html" class="hover:underline">Home</a>
        <span class="ml-2">|</span>
        <a href="/login.html" class="ml-2 hover:underline">Login</a>
      </nav>`;
  }
});

// Display guest UI
function showGuest(container) {
  if (!container) return;
  container.innerHTML = `
    <span class="text-white">Guest</span>
    (<a href="/login.html" class="text-pink-600 hover:underline">Login</a>)`;
}

// Display logged-in dropdown UI
function showLoggedIn(container, data) {
  if (!container) return;

  const userName = data.loggedIn_User || 'User';
  container.innerHTML = `
    <div class="relative inline-block text-left">
      <button id="userDropdownButton" class="bg-pink-600 text-white px-4 py-2 rounded">
        ${userName}
      </button>
      <div id="userDropdownMenu" class="hidden absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
        <a href="/users/profile.html" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">Profile</a>
        <a href="/users/cart.html" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">Cart</a>
        <a href="/users/orders.html" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">Orders</a>
        <a href="#" id="logoutLink" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">Logout</a>
      </div>
    </div>
  `;

  const dropdownButton = document.getElementById('userDropdownButton');
  const dropdownMenu = document.getElementById('userDropdownMenu');
  const logoutLink = document.getElementById('logoutLink');

  // Toggle dropdown
  if (dropdownButton && dropdownMenu) {
    dropdownButton.addEventListener('click', (e) => {
      e.stopPropagation(); // Prevent immediate close
      dropdownMenu.classList.toggle('hidden');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
      if (!dropdownButton.contains(e.target) && !dropdownMenu.contains(e.target)) {
        dropdownMenu.classList.add('hidden');
      }
    });
  }

  // Logout handler
  if (logoutLink) {
    logoutLink.addEventListener('click', (e) => {
      e.preventDefault();
      if (confirm("Are you sure you want to log out?")) {
        localStorage.removeItem('jwt');
        window.location.href = '/index.html';
      }
    });
  }
}

// Optional helper to require login
export function reqLogin() {
  const token = localStorage.getItem('jwt');
  if (!token) {
    window.location.href = '/redirects/401.html';
  }
}
