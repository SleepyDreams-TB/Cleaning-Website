document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("jwt");
  const billingForm = document.getElementById("billingForm");

  function showBillingMessage(type, message) {
    const billingMessage = document.getElementById("billingMessage");
    const billingIcon = document.getElementById("billingIcon");
    const billingText = document.getElementById("billingText");

    if (!billingMessage || !billingIcon || !billingText) return;

    // Class clean-up
    billingMessage.classList.remove(
      "hidden",
      "bg-green-100", "border-green-500",
      "bg-red-100", "border-red-500",
      "bg-blue-100", "border-blue-500"
    );

    if (type === "success") {
      billingIcon.className = "fas fa-check-circle text-green-500";
      billingMessage.classList.add("bg-green-100", "border-green-500");
    } else if (type === "error") {
      billingIcon.className = "fas fa-exclamation-triangle text-red-500";
      billingMessage.classList.add("bg-red-100", "border-red-500");
    } else {
      billingIcon.className = "fas fa-info-circle text-blue-500";
      billingMessage.classList.add("bg-blue-100", "border-blue-500");
    }

    billingText.textContent = message;
  }

  async function safeJson(res) {
    try {
      return await res.json();
    } catch {
      throw new Error("Invalid server response");
    }
  }

  async function fetchBillingInfo(userId) {
    try {
      const res = await fetch(`https://api.kingburger.site/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        throw new Error("Failed request");
      }

      const data = await safeJson(res);

      if (data.success && data.user.billing_info?.billing_address) {
        const addresses = Object.entries(
          data.user.billing_info.billing_address
        );

        if (addresses.length > 0) {
          const [addressName, info] = addresses[0];

          document.getElementById("address_name").value = addressName || "";
          document.getElementById("street").value = info.street || "";
          document.getElementById("city").value = info.city || "";
          document.getElementById("suburb").value = info.suburb || "";
          document.getElementById("postal_code").value =
            info.postal_code || "";
          document.getElementById("country").value = info.country || "";
        } else {
          showBillingMessage("info", "No billing info configured yet.");
        }
      } else {
        showBillingMessage("error", "Failed to fetch billing info.");
      }
    } catch (err) {
      console.error(err);
      showBillingMessage("error", "Error fetching billing info.");
    }
  }

  async function init() {
    if (!token) {
      window.location.href = "/redirects/401";
      return;
    }

    if (!billingForm) return;

    try {
      const res = await fetch(
        "https://api.kingburger.site/users/dashboard/info",
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!res.ok) {
        throw new Error("Failed request");
      }

      const data = await safeJson(res);

      if (data.success && data.user_id) {
        await fetchBillingInfo(data.user_id);
      } else {
        showBillingMessage("error", "Failed to fetch user info.");
        billingForm.style.display = "none";
      }
    } catch (err) {
      console.error(err);
      showBillingMessage("error", "Error fetching user info.");
      billingForm.style.display = "none";
    }
  }

  if (billingForm) {
    billingForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const billingData = {
        address_name: document
          .getElementById("address_name")
          .value.trim(),
        street: document.getElementById("street").value.trim(),
        city: document.getElementById("city").value.trim(),
        suburb: document.getElementById("suburb").value.trim(),
        postal_code: document
          .getElementById("postal_code")
          .value.trim(),
        country: document.getElementById("country").value.trim(),
      };

      try {
        const res = await fetch(
          "https://api.kingburger.site/users/update/billing/address",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(billingData),
          }
        );

        let result;
        try {
          result = await res.json();
        } catch {
          throw new Error("Invalid server response");
        }

        if (res.ok && result.success) {
          showBillingMessage(
            "success",
            "Billing info updated successfully."
          );
        } else {
          showBillingMessage(
            "error",
            result?.message || "Failed to update billing info."
          );
        }
      } catch (err) {
        console.error(err);
        showBillingMessage("error", "Error updating billing info.");
      }
    });
  }

  init();
});