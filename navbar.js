document.addEventListener('DOMContentLoaded', async () => {
  const navbarContainer = document.getElementById('navbar-container');
  if (!navbarContainer) return;

  try {
    const response = await fetch('/navbar.html');
    if (!response.ok) throw new Error();
    navbarContainer.innerHTML = await response.text();

    const usernameSpan = document.getElementById('userFname');
    const logoutLink = document.getElementById('logoutLink');
    const dropdownButton = document.getElementById('userDropdownButton');
    const dropdownMenu = document.getElementById('userDropdownMenu');
    const token = localStorage.getItem('jwt');

    // Show/Hide dropdown on click
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

    if (!token) {
      showGuest(usernameSpan, logoutLink);
      return;
    }

    try {
      const res = await fetch('https://api.kingburger.site/users/dashboard', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!res.ok) throw new Error();

      const responseData = await res.json();

      const user_data = responseData.user || {};
      if (usernameSpan) {
        usernameSpan.textContent = `${user_data.firstName || ''} ${user_data.lastName || ''}`.trim() || user_data.userName || 'User';
      }

    } catch {
      showGuest(usernameSpan, logoutLink);
    }

    if (logoutLink) {
      logoutLink.addEventListener('click', () => {
        if (confirm("Are you sure you want to log out?")) {
          localStorage.removeItem('jwt');
          window.location.href = '/index.html';
        }
      });
    }

  } catch {
    if (navbarContainer) {
      navbarContainer.innerHTML = `
        <nav class="bg-gray-900 text-white p-4 text-center">
          <a href="/index.html" class="hover:underline">Home</a>
          <span class="ml-2">|</span>
          <a href="/login.html" class="ml-2 hover:underline">Login</a>
        </nav>`;
    }
  }
});

// Helper function to show guest UI
function showGuest(usernameSpan, logoutLink) {
  if (usernameSpan) {
    usernameSpan.innerHTML = `
      <span class="text-white">Guest</span>
      (<a href="/login.html" class="text-pink-600 hover:underline">Login</a>)`;
  }
  if (logoutLink) logoutLink.style.display = 'none';
}

// Reusable function for requiring login
export function reqLogin() {
  const token = localStorage.getItem('jwt');
  if (!token) {
    window.location.href = '/redirects/401.html';
  }
}
