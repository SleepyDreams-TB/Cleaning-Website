// ================= Loader Setup =================
const loaderOverlay = document.createElement('div');
loaderOverlay.id = 'loaderOverlay';
loaderOverlay.style.cssText = `
  position: fixed; top:0; left:0; width:100%; height:100%;
  display:none; align-items:center; justify-content:center; background:rgba(0,0,0,0.3);
  z-index:9999;
`;
loaderOverlay.innerHTML = '<img src="/assets/loader.gif" alt="Loading..." style="width:100px;height:100px;">';
document.body.appendChild(loaderOverlay);

export const showLoader = () => loaderOverlay.style.display = 'flex';
export const hideLoader = () => loaderOverlay.style.display = 'none';

// ================= Original Fetch =================
// You should define this as the "base" fetch function if needed
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
