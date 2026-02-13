const PROTECTED_PATHS = [
  '/users/profile',
  '/users/billing',
  '/users/orders'
];

function isProtectedPage() {
  const currentPath = window.location.pathname;
  return PROTECTED_PATHS.some(path => currentPath.startsWith(path));
}

function isLoggedIn() {
  return !!localStorage.getItem('jwt')
}

export async function initNavbar(containerId = "navbar-container") {
  const container = document.getElementById(containerId);
  if (!container) return;

  try {
    // Load navbar HTML
    const response = await fetch("/navbar");
    if (!response.ok) throw new Error("Failed to fetch navbar HTML");
    container.innerHTML = await response.text();

    const dropdownContainer = container.querySelector("#dropdownContainer");
    if (!dropdownContainer) return;

    if (!isLoggedIn()) {
      // Show Login Button
      dropdownContainer.innerHTML = `
        <a href="/login" id="loginButton" class="login-btn">
          <i class="fas fa-sign-in-alt"></i> Login
        </a>
      `;

      if (isProtectedPage()) {
        sessionStorage.setItem('redirectAfterLogin', window.location.pathname);
        window.location.href = "/index";
      }
      return;
    }

    // Fetch user info
    try {
      const res = await fetch("https://api.kingburger.site/users/dashboard/info", {
        headers: { "Authorization": `Bearer ${localStorage.getItem('jwt')}` }
      });
      if (!res.ok) {
        localStorage.removeItem("jwt");
        if (window.location.pathname !== "/" && window.location.pathname !== "/index") {
          window.location.href = "/index";
        }
        throw new Error("Invalid token");
      }
      const data = await res.json();
      const userName = data.loggedIn_User || "User";
      const profile_ImageUrl = data.profileImageUrl || "https://media.kingburger.site/images/default-profile.png";

      // Inject username link + dropdown toggle
      dropdownContainer.innerHTML = `
        <!-- Profile Image -->
        <img src="${profile_ImageUrl}" alt="Profile Icon" class="profile-icon" style="width:40px; height:40px; border-radius:50%; border: 2px solid #667eea; cursor: pointer; transition: all 0.3s;">
              
        <!-- Dropdown toggle -->
        <div class="relative inline-block text-left">
          <button id="userDropdownButton" class="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-blue-700 text-white px-4 py-2 rounded-lg font-semibold hover:shadow-lg transition-all duration-300" style="font-size: 14px;">
            ${userName}
            <i class="bi bi-list text-lg"></i>
          </button>
          <div id="userDropdownMenu" class="hidden absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-1 z-50 border border-gray-100">
            <a href="/users/profile" class="flex items-center gap-3 px-4 py-3 text-gray-800 hover:bg-blue-50 hover:text-blue-600 transition-all">
              <i class="fas fa-user text-blue-600"></i> Profile
            </a>
            <a href="/users/billing" class="flex items-center gap-3 px-4 py-3 text-gray-800 hover:bg-blue-50 hover:text-blue-600 transition-all">
              <i class="fas fa-credit-card text-blue-600"></i> Billing
            </a>
            <a href="/users/cart" class="flex items-center gap-3 px-4 py-3 text-gray-800 hover:bg-blue-50 hover:text-blue-600 transition-all">
              <i class="fas fa-shopping-cart text-blue-600"></i> Cart
            </a>
            <a href="/users/orders" class="flex items-center gap-3 px-4 py-3 text-gray-800 hover:bg-blue-50 hover:text-blue-600 transition-all">
              <i class="fas fa-box text-blue-600"></i> Orders
            </a>
            <hr class="my-1">
            <a href="#" id="logoutLink" class="flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 transition-all font-semibold">
              <i class="fas fa-sign-out-alt"></i> Logout
            </a>
          </div>
        </div>
      `;

      // Dropdown toggle logic
      const dropdownButton = dropdownContainer.querySelector("#userDropdownButton");
      const dropdownMenu = dropdownContainer.querySelector("#userDropdownMenu");
      const profileIcon = dropdownContainer.querySelector(".profile-icon");
      const logoutLink = dropdownContainer.querySelector("#logoutLink");

      if (dropdownButton && dropdownMenu) {
        const toggleDropdown = (e) => {
          e.stopPropagation();
          dropdownMenu.classList.toggle("hidden");
        };

        dropdownButton.addEventListener("click", toggleDropdown);
        profileIcon?.addEventListener("click", toggleDropdown);

        document.addEventListener("click", e => {
          if (!dropdownButton.contains(e.target) && !dropdownMenu.contains(e.target) && !profileIcon?.contains(e.target)) {
            dropdownMenu.classList.add("hidden");
          }
        });
      }

      if (logoutLink) {
        logoutLink.addEventListener("click", e => {
          e.preventDefault();
          localStorage.removeItem("jwt");
          window.location.href = "/index";
        });
      }

    } catch (err) {
      console.error("Failed to fetch user info:", err);
      // Show Login Button on error
      dropdownContainer.innerHTML = `
        <a href="/login" id="loginButton" class="login-btn">
          <i class="fas fa-sign-in-alt"></i> Login
        </a>
      `;
    }

  } catch (err) {
    console.error("Failed to load navbar:", err);
    container.innerHTML = "<p class='text-red-500'>Navbar failed to load</p>";
  }
}