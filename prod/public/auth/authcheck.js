const CACHE_KEY = 'navbar_user_cache';
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes
 
const PROTECTED_PATHS = [
    '/users/profile',
    '/users/billing',
    '/users/orders',
    '/users/saved_cards'
];
 
// ------------------- Cache Helpers -------------------
 
export function getCachedUser() {
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
 
export function setCachedUser(data) {
  try {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify({ data, timestamp: Date.now() }));
  } catch {
    // sessionStorage full or unavailable — fail silently
  }
}
 
export function clearUserCache() {
  sessionStorage.removeItem(CACHE_KEY);
}
 
// ------------------- Route Helpers -------------------
 
export function isProtectedPage() {
  return PROTECTED_PATHS.some(path => window.location.pathname.startsWith(path));
}
 
// ------------------- Core Auth -------------------
 
/**
 * Fetch the current user from the backend using the httpOnly cookie.
 * On 401 — clears cache and redirects to /login if on a protected page.
 * Throws on any auth failure so callers can handle the logged-out state.
 */
export async function fetchUser() {
  const res = await fetch("https://api.kingburger.site/users/dashboard/info", {
    credentials: "include"  // httpOnly cookie sent automatically
  });
 
  if (!res.ok) {
    clearUserCache();
    if (isProtectedPage()) {
      sessionStorage.setItem('redirectAfterLogin', window.location.pathname);
      window.location.href = "/login";
    }
    throw new Error("Not authenticated");
  }
 
  const data = await res.json();
  setCachedUser(data);
  return data;
}
 
/**
 * Call this on any protected page that doesn't use the navbar.
 * Returns the user object or null (redirect already handled).
 * 
 * Usage:
 *   import { requireAuth } from '/auth/authcheck.js';
 *   const user = await requireAuth();
 *   if (!user) return;
 */
export async function requireAuth() {
  const cached = getCachedUser();
  if (cached) return cached;
 
  try {
    return await fetchUser();
  } catch {
    return null; // redirect already handled inside fetchUser
  }
}
 
    /**
     * Logout — clears the httpOnly cookie server-side, clears local cache,
     * then redirects to login. Always call this instead of just clearing cache.
     */
export async function logout() {
  try {
    await fetch("https://api.kingburger.site/auth/logout", {
      method: "POST",
      credentials: "include"
    });
  } catch (err) {
    console.error("Logout request failed:", err);
  }
  clearUserCache();
  window.location.href = "/login";
}
 
// ------------------- Cart Helper -------------------
 
export function updateCartCount() {
  const cart = JSON.parse(localStorage.getItem('checkoutCart') || '[]');
  document.querySelectorAll('.cart-badge').forEach(badge => {
    badge.textContent = cart.length;
  });
}