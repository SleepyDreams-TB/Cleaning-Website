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
