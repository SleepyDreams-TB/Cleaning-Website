import {
  getCachedUser,
  fetchUser,
  isProtectedPage,
  logout,
  updateCartCount
} from '/auth/authcheck.js';
 
// ------------------- UI Helpers -------------------
 
function applyUserToNavbar(container, data) {
  const profileUrl = data.profileImageUrl || "https://media.kingburger.site/images/default-profile.png";
  const userName = data.loggedIn_User || "User";
 
  const profileImage = container.querySelector("#profileImage");
  const userNameText = container.querySelector("#userNameText");
  const mobileProfileImage = container.querySelector("#mobileProfileImage");
  const mobileUserName = container.querySelector("#mobileUserName");
 
  if (profileImage) profileImage.src = profileUrl;
  if (userNameText) userNameText.textContent = userName;
  if (mobileProfileImage) mobileProfileImage.src = profileUrl;
  if (mobileUserName) mobileUserName.textContent = userName;
}
 
function bindLoggedInNavbar(container) {
  const loginButton = container.querySelector("#loginButton");
  const userDropdownButton = container.querySelector("#userDropdownButton");
  const mobileLoggedOut = container.querySelector("#mobileLoggedOut");
  const mobileLoggedIn = container.querySelector("#mobileLoggedIn");
  const dropdownMenu = container.querySelector("#userDropdownMenu");
  const logoutLink = container.querySelector("#logoutLink");
  const mobileLogoutLink = container.querySelector("#mobileLogoutLink");
 
  // Show logged-in UI, hide logged-out UI
  loginButton.classList.add("hidden");
  userDropdownButton.classList.remove("hidden");
  userDropdownButton.classList.add("flex");
  mobileLoggedOut.classList.add("hidden");
  mobileLoggedIn.classList.remove("hidden");
 
  // Desktop dropdown toggle
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
 
  // Logout — delegates entirely to authcheck.js
  const handleLogout = (e) => {
    e.preventDefault();
    logout();
  };
 
  if (logoutLink) logoutLink.addEventListener("click", handleLogout);
  if (mobileLogoutLink) mobileLogoutLink.addEventListener("click", handleLogout);
}
 
function bindLoggedOutNavbar(container) {
  const loginButton = container.querySelector("#loginButton");
  const userDropdownButton = container.querySelector("#userDropdownButton");
  const mobileLoggedOut = container.querySelector("#mobileLoggedOut");
  const mobileLoggedIn = container.querySelector("#mobileLoggedIn");
 
  loginButton.classList.remove("hidden");
  userDropdownButton.classList.add("hidden");
  mobileLoggedOut.classList.remove("hidden");
  mobileLoggedIn.classList.add("hidden");
 
  if (isProtectedPage()) {
    sessionStorage.setItem('redirectAfterLogin', window.location.pathname);
    window.location.href = "/login";
  }
}
 
// ------------------- Init -------------------
 
export async function initNavbar(containerId = "navbar-container") {
  const container = document.getElementById(containerId);
  if (!container) return console.error("Navbar container not found");
 
  try {
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
 
    // --- Auth: try cache first, then fetch ---
    const cached = getCachedUser();
 
    if (cached) {
      // Render instantly from cache
      bindLoggedInNavbar(container);
      applyUserToNavbar(container, cached);
      updateCartCount();
 
      // Silently revalidate in background
      fetchUser()
        .then(freshData => applyUserToNavbar(container, freshData))
        .catch(() => {
          // Cookie expired mid-session — fetchUser handles redirect
        });
 
    } else {
      // No cache — fetch and block until resolved
      try {
        const data = await fetchUser();
        bindLoggedInNavbar(container);
        applyUserToNavbar(container, data);
        updateCartCount();
      } catch {
        // Not authenticated — fetchUser handles protected page redirect
        bindLoggedOutNavbar(container);
        updateCartCount();
      }
    }
 
  } catch (err) {
    console.error("Failed to load navbar:", err);
    container.innerHTML = "<p class='text-red-500'>Navbar failed to load</p>";
  }
}
 
// Re-export updateCartCount so pages that only import navbar.js
// don't need a separate import for cart updates
export { updateCartCount };