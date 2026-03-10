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
  return !!localStorage.getItem('jwt');
}

// Update cart count
export function updateCartCount() {
  const cart = JSON.parse(localStorage.getItem('checkoutCart') || '[]');
  document.querySelectorAll('.cart-badge').forEach(badge => {
    badge.textContent = cart.length;
  });
}

export async function initNavbar(containerId = "navbar-container") {
  const container = document.getElementById(containerId);

  if (!container) return console.error("Navbar container not found in navbar");

  try {
    // Load navbar HTML
    const response = await fetch("/navbar.html");
    if (!response.ok) throw new Error("Failed to fetch navbar HTML");
    container.innerHTML = await response.text();

    // --- Hamburger toggle ---
    const hamburgerButton = container.querySelector("#hamburgerButton");
    const hamburgerIcon = container.querySelector("#hamburgerIcon");
    const mobileMenu = container.querySelector("#mobileMenu");

    if (hamburgerButton && mobileMenu) {
      hamburgerButton.addEventListener("click", () => {
        const isOpen = !mobileMenu.classList.contains("hidden");
        mobileMenu.classList.toggle("hidden", isOpen);
        hamburgerIcon.classList.toggle("fa-bars", isOpen);
        hamburgerIcon.classList.toggle("fa-times", !isOpen);
      });
    }

    // --- Auth state ---
    const loginButton = container.querySelector("#loginButton");
    const userDropdownButton = container.querySelector("#userDropdownButton");
    const mobileLoggedOut = container.querySelector("#mobileLoggedOut");
    const mobileLoggedIn = container.querySelector("#mobileLoggedIn");

    if (!isLoggedIn()) {
      // Desktop: show login button
      loginButton.classList.remove("hidden");
      userDropdownButton.classList.add("hidden");
      // Mobile: show login, hide user section
      mobileLoggedOut.classList.remove("hidden");
      mobileLoggedIn.classList.add("hidden");

      if (isProtectedPage()) {
        sessionStorage.setItem('redirectAfterLogin', window.location.pathname);
        window.location.href = "/index";
      }

      updateCartCount();
      return;
    }

    // Logged in — hide login, show user dropdown on desktop
    loginButton.classList.add("hidden");
    userDropdownButton.classList.remove("hidden");
    userDropdownButton.classList.add("flex");
    // Mobile: hide login, show user section
    mobileLoggedOut.classList.add("hidden");
    mobileLoggedIn.classList.remove("hidden");

    // Fetch user info
    try {
      const res = await fetch("https://api.kingburger.site/users/dashboard/info", {
        headers: { "Authorization": `Bearer ${localStorage.getItem('jwt')}` }
      });

      if (!res.ok) {
        localStorage.removeItem("jwt");
        if (isProtectedPage()) window.location.href = "/index";
        throw new Error("Invalid token");
      }

      const data = await res.json();
      const profileUrl = data.profileImageUrl || "https://media.kingburger.site/images/default-profile.png";
      const userName = data.loggedIn_User || "User";

      // --- Desktop dropdown ---
      const dropdownMenu = container.querySelector("#userDropdownMenu");
      const logoutLink = container.querySelector("#logoutLink");

      container.querySelector("#profileImage").src = profileUrl;
      container.querySelector("#userNameText").textContent = userName;

      if (userDropdownButton && dropdownMenu) {
        userDropdownButton.addEventListener("click", (e) => {
          e.stopPropagation();
          dropdownMenu.classList.toggle("hidden");
        });

        document.addEventListener("click", e => {
          if (!userDropdownButton.contains(e.target) && !dropdownMenu.contains(e.target)) {
            dropdownMenu.classList.add("hidden");
          }
        });
      }

      if (logoutLink) {
        logoutLink.addEventListener("click", () => {
          localStorage.removeItem("jwt");
          window.location.href = "/index";
        });
      }

      // --- Mobile user section ---
      container.querySelector("#mobileProfileImage").src = profileUrl;
      container.querySelector("#mobileUserName").textContent = userName;

      const mobileLogoutLink = container.querySelector("#mobileLogoutLink");
      if (mobileLogoutLink) {
        mobileLogoutLink.addEventListener("click", () => {
          localStorage.removeItem("jwt");
          window.location.href = "/index";
        });
      }

    } catch (err) {
      console.error("Failed to fetch user info:", err);
      // Fall back to showing login
      loginButton.classList.remove("hidden");
      userDropdownButton.classList.add("hidden");
      mobileLoggedOut.classList.remove("hidden");
      mobileLoggedIn.classList.add("hidden");
    }

    updateCartCount();

  } catch (err) {
    console.error("Failed to load navbar:", err);
    container.innerHTML = "<p class='text-red-500'>Navbar failed to load</p>";
  }
}