
// ================= Loader Setup =================
const loaderOverlay = document.createElement('div');
loaderOverlay.id = 'loaderOverlay';
loaderOverlay.style.cssText = `
  position: fixed; 
  top: 50%; 
  left: 50%; 
  transform: translate(-50%, -50%);
  display: none; 
  align-items: center; 
  justify-content: center; 
  z-index: 9999;
  background: transparent;
`;
loaderOverlay.innerHTML = '<img src="/assets/loader.gif" alt="Loading..." style="width:100px;height:100px;">';
document.body.appendChild(loaderOverlay);

export const showLoader = () => loaderOverlay.style.display = 'flex';
export const hideLoader = () => loaderOverlay.style.display = 'none';

// ================= Original Fetch =================
export async function originalApiFetch(...args) {
    return fetch(...args);
}

// ================= Global apiFetch Override =================
export async function apiFetch(...args) {
    showLoader();
    try {
        const response = await originalApiFetch(...args);
        return response; // raw Response object
    } catch (err) {
        throw err;
    } finally {
        hideLoader();
    }
}

/**
     * Security function: Escape HTML special characters to prevent XSS attacks
     * Converts dangerous characters to HTML entities
     * @param {string} text - Raw text that may contain HTML
     * @returns {string} Escaped safe HTML
     */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}
