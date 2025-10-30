import { reqLogin } from '../navbar.js';
reqLogin();

document.addEventListener('DOMContentLoaded', () => {
  let userId;
  const JWT = localStorage.getItem("jwt");
  if (!JWT) window.location.href = "../index.html";

  try {
    const payload = jwt_decode(JWT);
    userId = payload.user_id;
    console.log("Decoded JWT userId:", userId);
  } catch (e) {
    console.error("Failed to decode JWT:", e);
    window.location.href = "../index.html";
  }

  async function loadNavbar() {
    try {
      const response = await fetch("/navbar.html");
      if (!response.ok) throw new Error("Failed to load navbar");
      const html = await response.text();
      document.getElementById("navbar-container").innerHTML = html;

      // Import navbar logic after HTML is injected
      import('../navbar.js'); // this attaches dropdown events

    } catch (error) {
      console.error("Error loading navbar:", error);
      document.getElementById("navbar-container").innerHTML =
        '<p class="text-red-500">Navbar failed to load</p>';
    }
  }
  loadNavbar();

  // Fetch user data
  async function fetchUser() {
    try {
      const response = await fetch(`https://api.kingburger.site/users/${userId}`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${JWT}` }
      });
      if (!response.ok) throw new Error("Failed to fetch user");
      const responseData = await response.json();
      const userData = responseData.user || {};

      const fields = {
        username: userData.userName || "",
        fname: userData.firstName || "",
        lname: userData.lastName || "",
        email: userData.email || "",
        cellnumber: userData.cellNum || "",
        createdDate: userData.created_at || ""
      };

      Object.entries(fields).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) el.value = value;
      });
    } catch (error) {
      console.error("Error fetching user:", error);
    }
  }
  fetchUser();

  // Enable editing
  function enableField(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) {
      field.disabled = false;
      field.focus();
    }
  }

  // Map edit buttons to fields
  const editButtons = [
    { btnId: "editUsernameBtn", fieldId: "username" },
    { btnId: "editPasswordBtn", fieldId: "password" },
    { btnId: "editFnameBtn", fieldId: "fname" },
    { btnId: "editLnameBtn", fieldId: "lname" },
    { btnId: "editEmailBtn", fieldId: "email" },
    { btnId: "editCellBtn", fieldId: "cellnumber" }
  ];

  editButtons.forEach(item => {
    const btn = document.getElementById(item.btnId);
    if (btn) btn.addEventListener('click', () => enableField(item.fieldId));
  });

  // Username availability check
  async function checkUsernameAvailability() {
    const username = document.getElementById('username')?.value || "";
    const email = document.getElementById('email')?.value || "";
    if (!username) return;

    try {
      const response = await fetch('/api/check_user_avail', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email })
      });
      if (!response.ok) return;
      const data = await response.json();
      const hint = document.getElementById('username-hint');
      if (hint) {
        hint.textContent = data.exists ? "Username already taken" : "Username is available";
        hint.style.color = data.exists ? "red" : "green";
      }
    } catch (error) {
      console.error("Error checking username:", error);
    }
  }

  // Password validation
  function validatePassword() {
    const password = document.getElementById('password')?.value || "";
    const hint = document.getElementById('password-hint');
    const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{12,}$/;
    if (hint) {
      if (regex.test(password)) {
        hint.textContent = "Password is strong";
        hint.style.color = "green";
      } else {
        hint.textContent = "Password must contain 1 lowercase, 1 uppercase, 1 number, 1 special character, min 12 chars";
        hint.style.color = "red";
      }
    }
  }

  document.getElementById('username')?.addEventListener('input', checkUsernameAvailability);
  document.getElementById('password')?.addEventListener('input', validatePassword);

  // Update profile
  document.getElementById('updateBtn')?.addEventListener('click', async () => {
    const data = new URLSearchParams();
    ["username", "password", "fname", "lname", "email", "cellnumber"].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        const key = id === "username" ? "userName" : id === "cellnumber" ? "cellNum" : id;
        data.append(key, el.value || "");
      }
    });

    try {
      const response = await fetch(`https://api.kingburger.site/users/update/${userId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${JWT}`,
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: data.toString()
      });

      const jsonResponse = await response.json();
      console.log("API response:", jsonResponse);

      if (!response.ok) throw new Error("Failed to update user");
      alert("Profile updated successfully!");

      ["username", "password", "fname", "lname", "email", "cellnumber"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = true;
      });

      window.location.reload();

    } catch (error) {
      console.error("Error updating profile:", error);
      alert("Failed to update profile. Check console.");
    }
  });
});
