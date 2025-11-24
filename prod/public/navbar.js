export async function initNavbar(containerId = "navbar-container") {
  const container = document.getElementById(containerId);
  if (!container) return;

  try {
    // Load navbar HTML
    const response = await fetch("/navbar.html");
    container.innerHTML = await response.text();

    const dropdownContainer = container.querySelector("#dropdownContainer");
    if (!dropdownContainer) return;

    const token = localStorage.getItem("jwt");
    if (!token) {
      dropdownContainer.innerHTML = `
        <span class="text-white">Guest</span>
        (<a href="/login.html" class="text-pink-600 hover:underline">Login</a>)
      `;
      return;
    }

    try {
      const res = await fetch('https://api.kingburger.site/users/dashboard/info', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Invalid token');
      const data = await res.json();
      const userName = data.loggedIn_User || 'User';

      // Inject dual-button layout
      dropdownContainer.innerHTML = `
        <!-- Username direct link -->
        <a href="/users/profile.html" class="bg-pink-600 text-white px-4 py-2 rounded">
          ${userName}
        </a>

        <!-- Dropdown toggle -->
        <div class="relative inline-block text-left">
          <button id="userDropdownButton" class="bg-pink-600 text-white px-4 py-2 rounded">
            <i class="bi bi-list"></i>
          </button>
          <div id="userDropdownMenu" class="hidden absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
            <a href="/users/cart.html" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">Cart</a>
            <a href="/users/orders.html" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">Orders</a>
            <a href="#" id="logoutLink" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">Logout</a>
          </div>
        </div>
      `;

      // Dropdown JS
      const dropdownButton = dropdownContainer.querySelector("#userDropdownButton");
      const dropdownMenu = dropdownContainer.querySelector("#userDropdownMenu");
      const logoutLink = dropdownContainer.querySelector("#logoutLink");

      if (dropdownButton && dropdownMenu) {
        dropdownButton.addEventListener("click", e => {
          e.stopPropagation();
          dropdownMenu.classList.toggle("hidden");
        });

        document.addEventListener("click", e => {
          if (!dropdownButton.contains(e.target) && !dropdownMenu.contains(e.target)) {
            dropdownMenu.classList.add("hidden");
          }
        });
      }

      if (logoutLink) {
        logoutLink.addEventListener("click", e => {
          e.preventDefault();
          localStorage.removeItem("jwt");
          window.location.href = "/index.html";
        });
      }

    } catch (err) {
      console.error("Failed to load user dropdown:", err);
      dropdownContainer.innerHTML = `
        <span class="text-white">Guest</span>
        (<a href="/login.html" class="text-pink-600 hover:underline">Login</a>)
      `;
    }

  } catch (err) {
    console.error("Failed to load navbar:", err);
    container.innerHTML = "<p class='text-red-500'>Navbar failed to load</p>";
  }
}
