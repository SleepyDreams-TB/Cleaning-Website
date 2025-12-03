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

    // Check login token
    const token = localStorage.getItem("jwt");
    if (!token) {
      dropdownContainer.innerHTML = `
        <span>Guest</span>
        (<a href="/login" class="text-pink-600 hover:underline">Login</a>)
      `;

      if (window.location.pathname !== "/" && window.location.pathname !== "/index") {
        window.location.href = "/index";
      }
      return;
    }

    // Fetch user info
    try {
      const res = await fetch("https://api.kingburger.site/users/dashboard/info", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (!res.ok) {
        localStorage.removeItem("jwt");
        if (window.location.pathname !== "/" && window.location.pathname !== "/index") {
          window.location.href = "/index";

        } throw new Error("Invalid token");
      }
      const data = await res.json();
      const userName = data.loggedIn_User || "User";
      const profile_ImageUrl = data.profileImageUrl || "https://media.kingburger.site/images/default-profile.png";
      // Inject username link + dropdown toggle
      dropdownContainer.innerHTML = `
        <!-- Username link -->
        <img src="${profile_ImageUrl}" alt="Profile Icon" class="profile-icon" style="width:40px; height:40px; border-radius:50%;">
              
        <!-- Dropdown toggle -->
        <div class="relative inline-block text-left">
          <button id="userDropdownButton" class="bg-pink-600 text-white px-4 py-2 rounded">
            ${userName}
            <i class="bi bi-list"></i>
          </button>
          <div id="userDropdownMenu" class="hidden absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
            <a href="/users/profile" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">Profile</a>
            <a href="/users/billing" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">Billing</a>
            <a href="/users/cart" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">Cart</a>
            <a href="/users/orders" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">Orders</a>
            <a href="#" id="logoutLink" class="block px-4 py-2 text-gray-800 hover:bg-gray-100">Logout</a>
          </div>
        </div>
      `;

      // Dropdown toggle logic
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
          window.location.href = "/index";
        });
      }

    } catch (err) {
      console.error("Failed to fetch user info:", err);
      dropdownContainer.innerHTML = `
        <span>Guest</span>
        (<a href="/login" class="text-pink-600 hover:underline">Login</a>)
      `;
    }

  } catch (err) {
    console.error("Failed to load navbar:", err);
    container.innerHTML = "<p class='text-red-500'>Navbar failed to load</p>";
  }
}
