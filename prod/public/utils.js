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
import { config } from "../config.js";

//API Fetch wrapper - import on each page 

export async function apiFetch(path, options = {}) {
    const token = localStorage.getItem("jwt");

    const res = await fetch(`${config.BACKEND_URL}${path}`, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...options.headers,
        },
    });

    if (res.status === 401) {
        localStorage.removeItem("jwt");
        sessionStorage.removeItem("navbar_user_cache");
        window.location.href = "/redirects/401";
        return null;
    }

    let data = null;
    try {
        data = await res.json();
    } catch {
        throw new Error("Invalid server response");
    }

    return { ok: res.ok, status: res.status, data };
}

export async function safeJson(res) {
    if (!res) return null;
    try {
        return await res.json();
    } catch {
        throw new Error("Invalid server response");
    }
}