import { apiFetch } from '/utils.js';

document.addEventListener("DOMContentLoaded", () => {
  const billingForm = document.getElementById("billingForm");
  const addressList = document.getElementById("addressList");
  const addNewBtn = document.getElementById("addNewBtn");
  const formTitle = document.getElementById("formTitle");
  const submitBtn = document.getElementById("submitBtn");
  const cancelBtn = document.getElementById("cancelBtn");

  let allAddresses = {};
  let editingKey = null;

  // ─── Message Helper ────────────────────────────────────────────────────────

  function showMessage(type, message) {
    const box = document.getElementById("billingMessage");
    const icon = document.getElementById("billingIcon");
    const text = document.getElementById("billingText");
    if (!box || !icon || !text) return;

    box.classList.remove(
      "hidden",
      "bg-green-100", "border-green-500",
      "bg-red-100", "border-red-500",
      "bg-blue-100", "border-blue-500"
    );

    if (type === "success") {
      icon.className = "fas fa-check-circle text-green-500";
      box.classList.add("bg-green-100", "border-green-500");
    } else if (type === "error") {
      icon.className = "fas fa-exclamation-triangle text-red-500";
      box.classList.add("bg-red-100", "border-red-500");
    } else {
      icon.className = "fas fa-info-circle text-blue-500";
      box.classList.add("bg-blue-100", "border-blue-500");
    }

    text.textContent = message;
    setTimeout(() => box.classList.add("hidden"), 4000);
  }

  // ─── Render Address List ───────────────────────────────────────────────────

  function renderAddressList() {
    if (!addressList) return;
    const entries = Object.entries(allAddresses);

    if (entries.length === 0) {
      addressList.innerHTML = `
        <p class="text-gray-400 text-sm text-center py-4">No saved addresses yet. Add one below.</p>
      `;
      return;
    }

    addressList.innerHTML = entries.map(([name, info]) => `
      <div class="address-card" data-key="${name}">
        <div class="address-card-info">
          <div class="address-card-name">
            <i class="fas fa-map-marker-alt"></i> ${name}
          </div>
          <div class="address-card-detail">
            ${info.street}, ${info.suburb}, ${info.city}, ${info.postal_code}, ${info.country}
          </div>
        </div>
        <div class="address-card-actions">
          <button class="btn-edit" data-key="${name}">
            <i class="fas fa-pen"></i> Edit
          </button>
          
        </div>
      </div>
    `).join("");

    /*<button class="btn-delete" data-key="${name}">
                <i class="fas fa-trash"></i>
              </button>
    */
    addressList.querySelectorAll(".btn-edit").forEach(btn => {
      btn.addEventListener("click", () => loadAddressIntoForm(btn.dataset.key));
    });

    addressList.querySelectorAll(".btn-delete").forEach(btn => {
      btn.addEventListener("click", () => deleteAddress(btn.dataset.key));
    });
  }

  // ─── Load Address Into Form ────────────────────────────────────────────────

  function loadAddressIntoForm(key) {
    const info = allAddresses[key];
    if (!info) return;

    editingKey = key;
    formTitle.textContent = `Editing: ${key}`;
    document.getElementById("address_name").value = key;
    document.getElementById("street").value = info.street || "";
    document.getElementById("city").value = info.city || "";
    document.getElementById("suburb").value = info.suburb || "";
    document.getElementById("postal_code").value = info.postal_code || "";
    document.getElementById("country").value = info.country || "";

    billingForm.scrollIntoView({ behavior: "smooth" });
    cancelBtn.classList.remove("hidden");
  }

  // ─── Reset Form ────────────────────────────────────────────────────────────

  function resetForm() {
    editingKey = null;
    formTitle.textContent = "Add New Address";
    billingForm.reset();
    document.getElementById("country").value = "South Africa";
    cancelBtn.classList.add("hidden");
  }

  // ─── Delete Address ────────────────────────────────────────────────────────

  async function deleteAddress(key) {
    if (!confirm(`Delete address "${key}"?`)) return;

    const updatedAddresses = { ...allAddresses };
    delete updatedAddresses[key];

    const result = await apiFetch("/users/update/billing/address", {
      method: "POST",
      body: JSON.stringify({
        replace_all: true,
        addresses: updatedAddresses,
      }),
    });

    if (!result) return; // 401

    const { ok, data } = result;

    if (ok && data?.success) {
      allAddresses = updatedAddresses;
      renderAddressList();
      showMessage("success", `Address "${key}" deleted.`);
      if (editingKey === key) resetForm();
    } else {
      showMessage("error", data?.message || "Failed to delete address.");
    }
  }

  // ─── Fetch Billing Info ────────────────────────────────────────────────────

  async function fetchBillingInfo(userId) {
    const result = await apiFetch(`/users/${userId}`);
    if (!result) return; // 401

    const { ok, data } = result;

    if (!ok) {
      showMessage("error", "Failed to fetch billing info.");
      return;
    }

    if (data?.success && data.user?.billing_info?.billing_address) {
      allAddresses = data.user.billing_info.billing_address;
      renderAddressList();
    } else {
      showMessage("info", "No billing info configured yet.");
    }
  }

  // ─── Init ──────────────────────────────────────────────────────────────────

  async function init() {
    if (!localStorage.getItem("jwt")) {
      window.location.href = "/redirects/401";
      return;
    }

    if (!billingForm) return;

    const result = await apiFetch("/users/dashboard/info");
    if (!result) return; // 401

    const { ok, data } = result;

    if (!ok) {
      showMessage("error", "Failed to fetch user info.");
      billingForm.style.display = "none";
      return;
    }

    if (data?.success && data.user_id) {
      await fetchBillingInfo(data.user_id);
    } else {
      showMessage("error", "Failed to fetch user info.");
      billingForm.style.display = "none";
    }
  }

  // ─── Form Submit ───────────────────────────────────────────────────────────

  if (billingForm) {
    billingForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      submitBtn.disabled = true;
      submitBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Saving...`;

      const addressName = document.getElementById("address_name").value.trim();
      const newEntry = {
        street: document.getElementById("street").value.trim(),
        city: document.getElementById("city").value.trim(),
        suburb: document.getElementById("suburb").value.trim(),
        postal_code: document.getElementById("postal_code").value.trim(),
        country: document.getElementById("country").value.trim(),
      };

      const updatedAddresses = { ...allAddresses };
      if (editingKey && editingKey !== addressName) {
        delete updatedAddresses[editingKey];
      }
      updatedAddresses[addressName] = newEntry;

      try {
        const result = await apiFetch("/users/update/billing/address", {
          method: "POST",
          body: JSON.stringify({
            address_name: addressName,
            ...newEntry,
          }),
        });

        if (!result) return;

        const { ok, data } = result;

        if (ok && data?.success) {
          allAddresses = updatedAddresses;
          renderAddressList();
          showMessage("success", "Address saved successfully.");
          resetForm();
        } else {
          showMessage("error", data?.message || "Failed to save address.");
        }
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `<i class="fas fa-save"></i> Save Address`;
      }
    });
  }

  if (addNewBtn) addNewBtn.addEventListener("click", resetForm);
  if (cancelBtn) cancelBtn.addEventListener("click", resetForm);

  init();
});