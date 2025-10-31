// navbar.js
export function initNavbar(containerId = "navbar-container") {
  const container = document.getElementById(containerId);
  if (!container) return;

  const token = localStorage.getItem('jwt');

  // Show guest view if no token
  if (!token) {
    container.innerHTML = `<span>Guest</span> (<a href="/login.html">Login</a>)`;
    return;
  }

  // Fetch logged-in user info
  fetch('https://api.kingburger.site/users/dashboard/info', {
    headers: { 'Authorization': `Bearer ${token}` }
  })
    .then(res => res.json())
    .then(data => {
      container.innerHTML = `
        <div class="relative inline-block text-left" id="profileContainer">
          <button id="userDropdownButton" class="bg-pink-600 text-white px-4 py-2 rounded">
            ${data.loggedIn_User || 'User'}
          </button>
          <div id="userDropdownMenu" class="hidden absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
            <a href="/users/profile.html" class="block px-4 py-2 hover:bg-gray-100">Profile</a>
            <a href="/users/cart.html" class="block px-4 py-2 hover:bg-gray-100">Cart</a>
            <a href="/users/orders.html" class="block px-4 py-2 hover:bg-gray-100">Orders</a>
            <a href="#" id="logoutLink" class="block px-4 py-2 hover:bg-gray-100">Logout</a>
          </div>
        </div>
      `;

      // Dropdown toggle
      const dropdownButton = document.getElementById('userDropdownButton');
      const dropdownMenu = document.getElementById('userDropdownMenu');
      const logoutLink = document.getElementById('logoutLink');

      dropdownButton.addEventListener('click', e => {
        e.stopPropagation();
        dropdownMenu.classList.toggle('hidden');
      });

      // Close dropdown when clicking outside
      document.addEventListener('click', e => {
        if (!dropdownButton.contains(e.target) && !dropdownMenu.contains(e.target)) {
          dropdownMenu.classList.add('hidden');
        }
      });

      logoutLink.addEventListener('click', e => {
        e.preventDefault();
        localStorage.removeItem('jwt');
        window.location.href = '/index.html';
      });

    })
    .catch(() => {
      container.innerHTML = `<span>Guest</span> (<a href="/login.html">Login</a>)`;
    });
}

// Optional helper to require login
export function reqLogin() {
  const token = localStorage.getItem('jwt');
  if (!token) window.location.href = '/redirects/401.html';
}
