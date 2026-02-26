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

// Update cart count
export function updateCartCount() {
  const cart = JSON.parse(localStorage.getItem('checkoutCart') || '[]');
  const cartBadge = document.querySelector('.cart-badge');
  if (cartBadge) {
    cartBadge.textContent = cart.length;
  }
}

export async function initNavbar(containerId = "navbar-container") {
  const container = document.getElementById(containerId);

  if (!container) return console.error("Navbar container not found in navbar");

  try {
    // Load navbar HTML
    const response = await fetch("./testNavbar.html");
    if (!response.ok) throw new Error("Failed to fetch navbar HTML");
    container.innerHTML = await response.text();

    const loginButton = container.querySelector("#loginButton");
    const userDropdownButton = container.querySelector("#userDropdownButton");


    if (!isLoggedIn()) {
      // Show Login Button
      loginButton.classList.remove("hidden");
      userDropdownButton.classList.add("hidden");

      if (isProtectedPage()) {
        sessionStorage.setItem('redirectAfterLogin', window.location.pathname);
        window.location.href = "/index";
      }
      return;
    } else {
      // Show User Dropdown
      loginButton.classList.add("hidden");
      userDropdownButton.classList.remove("hidden");
      userDropdownButton.classList.add("flex");
    }

    // Fetch user info
    try {
      const res = await fetch("https://api.kingburger.site/users/dashboard/info", {
        headers: { "Authorization": `Bearer ${localStorage.getItem('jwt')}` }
      });
      if (!res.ok) {
        localStorage.removeItem("jwt");
        if (isProtectedPage()) {
          window.location.href = "/index";
        }
        throw new Error("Invalid token");
      }

      const data = await res.json();

      // Dropdown toggle logic
      const dropdownMenu = container.querySelector("#userDropdownMenu");
      const logoutLink = container.querySelector("#logoutLink");

      userDropdownButton.querySelector("#profileImage").src = data.profileImageUrl || "https://media.kingburger.site/images/default-profile.png";
      userDropdownButton.querySelector("#userNameText").textContent = data.loggedIn_User || "User";

      if (userDropdownButton && dropdownMenu) {
        userDropdownButton.addEventListener("click", () => {
          dropdownMenu.classList.toggle("hidden");
        });

        document.addEventListener("click", e => {
          if (!userDropdownButton.contains(e.target) && !dropdownMenu.contains(e.target)) {
            dropdownMenu.classList.add("hidden");
          }
        });
      }

      if (logoutLink) {
        logoutLink.addEventListener("click", e => {
          localStorage.removeItem("jwt");
          window.location.href = "/index";
        });
      }

    } catch (err) {
      console.error("Failed to fetch user info:", err);
      // Show Login Button on error
      loginButton.classList.remove("hidden");
      userDropdownButton.classList.add("hidden");
    }

  } catch (err) {
    console.error("Failed to load navbar:", err);
    container.innerHTML = "<p class='text-red-500'>Navbar failed to load</p>";
  }
}