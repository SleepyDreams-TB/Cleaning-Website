document.addEventListener('DOMContentLoaded', async () => {
  const navbarContainer = document.getElementById('navbar-container');
  if (!navbarContainer) return;

  try {
    const response = await fetch('/navbar.html');
    if (!response.ok) throw new Error();
    navbarContainer.innerHTML = await response.text();

    const profileContainer = document.getElementById('profileContainer'); // Single container for guest or logged-in
    const token = localStorage.getItem('jwt');

    // Swap content based on login status
    if (!token) {
      showGuest(profileContainer);
      return;
    }

    try {
      const res = await fetch('https://api.kingburger.site/users/dashboard/info', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!res.ok) throw new Error();

      const responseData = await res.json();
      showLoggedIn(profileContainer, responseData);

    } catch {
      showGuest(profileContainer);
    }

  } catch {
    navbarContainer.innerHTML = `
      <nav class="bg-gray-900 text-white p-4 text-center">
        <a href="/index.html" class="hover:underline">Home</a>
        <span class="ml-2">|</span>
        <a href="/login.html" class="ml-2 hover:underline">Login</a>
      </nav>`;
  }
});

// Show guest/login UI
function showGuest(container) {
  if (!container) return;
  container.innerHTML = `
    <span class="text-white">Guest</span>
    (<a href="/login.html" class="text-pink-600 hover:underline">Login</a>)`;
}

// Show logged-in dropdown UI
function showLoggedIn(container, data) {
  if (!container) return;

  const userName = data.loggedIn_User || 'User';
  container.innerHTML = `
    <div class="relative inline-block text-left">
      <button id="userDropdownButton" class="bg-pink-600 text-white px-4 py-2 rounded">
        ${userName}
      </button>
      <div id="userDropdownMenu" class="hidden absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-20">
        <a href="/profile.html" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">Profile</a>
        <a href="#" id="logoutLink" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">Logout</a>
      </div>
    </div>
  `;

  const dropdownButton = document.getElementById('userDropdownButton');
  const dropdownMenu = document.getElementById('userDropdownMenu');
  const logoutLink = document.getElementById('logoutLink');

  // Toggle dropdown
  if (dropdownButton && dropdownMenu) {
    dropdownButton.addEventListener('click', () => {
      dropdownMenu.classList.toggle('hidden');
    });

    document.addEventListener('click', (e) => {
      if (!dropdownButton.contains(e.target) && !dropdownMenu.contains(e.target)) {
        dropdownMenu.classList.add('hidden');
      }
    });
  }

  // Logout
  if (logoutLink) {
    logoutLink.addEventListener('click', () => {
      if (confirm("Are you sure you want to log out?")) {
        localStorage.removeItem('jwt');
        window.location.href = '/index.html';
      }
    });
  }
}

// Require login helper
export function reqLogin() {
  const token = localStorage.getItem('jwt');
  if (!token) {
    window.location.href = '/redirects/401.html';
  }
}
