const billingForm = document.getElementById("billingForm");
const billingMessage = document.getElementById("billingMessage");
const token = localStorage.getItem("jwt");

// Redirect to 401.html if user is not logged in
if (!token) {
  window.location.href = "/401.html";
} else {
  fetch("https://api.kingburger.site/users/dashboard/info", {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then(res => res.json())
    .then(data => {
      if (data.success && data.user_id) {
        fetchBillingInfo(data.user_id);
      } else {
        billingMessage.textContent = "Could not fetch user info.";
        billingForm.style.display = "none";
      }
    })
    .catch(err => {
      console.error(err);
      billingMessage.textContent = "Error fetching user info.";
      billingForm.style.display = "none";
    });
}

function fetchBillingInfo(userId) {
  fetch(`https://api.kingburger.site/users/${userId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then(res => res.json())
    .then(data => {
      if (data.success && data.user.billing_info?.billing_address) {
        const addresses = Object.entries(data.user.billing_info.billing_address);
        if (addresses.length > 0) {
          const [addressName, info] = addresses[0];

          document.getElementById("address_name").value = addressName || "";
          document.getElementById("street").value = info.street || "";
          document.getElementById("city").value = info.city || "";
          document.getElementById("suburb").value = info.suburb || "";
          document.getElementById("postal_code").value = info.postal_code || "";
          document.getElementById("country").value = info.country || "";
        } else {
          billingMessage.textContent = "No billing info configured yet.";
        }
      } else {
        billingMessage.textContent = "No billing info configured yet.";
      }
    })
    .catch(err => {
      console.error(err);
      billingMessage.textContent = "Error fetching billing info.";
    });
}

billingForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const billingData = {
    address_name: document.getElementById("address_name").value.trim(),
    street: document.getElementById("street").value.trim(),
    city: document.getElementById("city").value.trim(),
    state: document.getElementById("state").value.trim(),
    zip: document.getElementById("zip").value.trim(),
    country: document.getElementById("country").value.trim(),
  };

  try {
    const res = await fetch("https://api.kingburger.site/users/update/billing/address", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(billingData),
    });

    const result = await res.json();
    if (res.ok && result.success) {
      billingMessage.textContent = result.message || "Billing info updated successfully.";
      billingMessage.classList.remove("text-red-600");
      billingMessage.classList.add("text-green-600");
    } else {
      billingMessage.textContent = result.detail || "Failed to update billing info.";
      billingMessage.classList.remove("text-green-600");
      billingMessage.classList.add("text-red-600");
    }
  } catch (err) {
    console.error(err);
    billingMessage.textContent = "Error updating billing info.";
    billingMessage.classList.remove("text-green-600");
    billingMessage.classList.add("text-red-600");
  }
});
