// ================= Loader Setup =================
const loaderOverlay = document.createElement('div');
loaderOverlay.id = 'loaderOverlay';
loaderOverlay.style.cssText = `
  position: fixed; top:0; left:0; width:100%; height:100%;
  display:none; align-items:center; justify-content:center; background:rgba(0,0,0,0.3);
  z-index:9999;
`;
loaderOverlay.innerHTML = '<img src="loader.gif" alt="Loading..." style="width:100px;height:100px;">';
document.body.appendChild(loaderOverlay);

window.showLoader = () => loaderOverlay.style.display = 'flex';
window.hideLoader = () => loaderOverlay.style.display = 'none';

// ================= Global Fetch Override =================
const originalFetch = window.fetch;

window.fetch = async (...args) => {
    showLoader(); // show loader automatically
    try {
        const response = await originalFetch(...args);
        return response;
    } catch (err) {
        throw err; // propagate error
    } finally {
        hideLoader(); // hide loader automatically
    }
};

// ================= Optional JSON Helper =================
window.apiFetch = async (url, options = {}) => {
    const res = await fetch(url, options); // uses overridden fetch
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Unknown error');
    return data;
};
