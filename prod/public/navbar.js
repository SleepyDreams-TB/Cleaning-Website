const PROTECTED_PATHS = [
  '/users/profile',
  '/users/billing',
  '/users/orders',
  '/users/saved_cards'
];

import { config } from "../config.js";

const CACHE_KEY = 'navbar_user_cache';
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

function isProtectedPage() {
  const currentPath = window.location.pathname;
  return PROTECTED_PATHS.some(path => currentPath.startsWith(path));
}

function isLoggedIn() {
  return !!localStorage.getItem('jwt');
}

function getCachedUser() {
  try {
    const raw = sessionStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const { data, timestamp } = JSON.parse(raw);
    if (Date.now() - timestamp > CACHE_TTL_MS) {
      sessionStorage.removeItem(CACHE_KEY);
      return null;
    }
    return data;
  } catch {
    return null;
  }
}

function setCachedUser(data) {
  try {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify({ data, timestamp: Date.now() }));
  } catch {
    // sessionStorage full or unavailable — fail silently
  }
}

function clearUserCache() {
  sessionStorage.removeItem(CACHE_KEY);
}

export function updateCartCount() {
  const cart = JSON.parse(localStorage.getItem('checkoutCart') || '[]');
  document.querySelectorAll('.cart-badge').forEach(badge => {
    badge.textContent = cart.length;
  });
}

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

async function fetchAndCacheUser(container) {
  const res = await fetch(`${config.BACKEND_URL}/users/dashboard/info`, {
    headers: { "Authorization": `Bearer ${localStorage.getItem('jwt')}` }
  });

  if (!res.ok) {
    // Token is invalid — clear everything and redirect if on protected page
    localStorage.removeItem("jwt");
    clearUserCache();
    if (isProtectedPage()) window.location.href = "/index";
    throw new Error("Invalid token");
  }

  const data = await res.json();
  setCachedUser(data);
  return data;
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

  // Logout — clear JWT and cache
  const handleLogout = () => {
    localStorage.removeItem("jwt");
    clearUserCache();
    window.location.href = "/index";
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
    window.location.href = "/index";
  }
}

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

    // --- Auth check ---
    if (!isLoggedIn()) {
      bindLoggedOutNavbar(container);
      updateCartCount();
      return;
    }

    // --- Logged in: check cache first ---
    const cached = getCachedUser();

    if (cached) {
      // Render instantly from cache
      bindLoggedInNavbar(container);
      applyUserToNavbar(container, cached);
      updateCartCount();

      // Silently revalidate in the background
      fetchAndCacheUser(container)
        .then(freshData => {
          // Update UI if something changed (e.g. new profile pic)
          applyUserToNavbar(container, freshData);
        })
        .catch(() => {
          // Token went invalid mid-session — already handled inside fetchAndCacheUser
        });

    } else {
      // No cache — fetch, block render until we have data (first load)
      try {
        const data = await fetchAndCacheUser(container);
        bindLoggedInNavbar(container);
        applyUserToNavbar(container, data);
        updateCartCount();
      } catch {
        // fetchAndCacheUser already handles redirect/cleanup on 401
        bindLoggedOutNavbar(container);
        updateCartCount();
      }
    }

  } catch (err) {
    console.error("Failed to load navbar:", err);
    container.innerHTML = "<p class='text-red-500'>Navbar failed to load</p>";
  }
}