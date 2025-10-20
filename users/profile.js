import { reqLogin } from '../navbar.js';
reqLogin();

document.addEventListener('DOMContentLoaded', () => {
  // Global variables
  let userId;
  const JWT = localStorage.getItem("jwt");
  if (!JWT) window.location.href = "../index.html";

  // Decode JWT
  try {
    const payload = jwt_decode(JWT);
    userId = payload.user_id;
    console.log("Decoded JWT userId:", userId);
  } catch (e) {
    console.error("Failed to decode JWT:", e);
    window.location.href = "../index.html";
  }

  // Load navbar
  async function loadNavbar() {
    try {
      const response = await fetch("../navbar.html");
      const html = await response.text();
      document.getElementById("navbar-container").innerHTML = html;
    } catch (error) {
      console.error("Error loading navbar:", error);
    }
  }
  loadNavbar();

  // Fetch user data
  async function fetchUser() {
    try {
      const response = await fetch(`https://api.kingburger.site/users/${userId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${JWT}`
        }
      });
      if (!response.ok) throw new Error("Failed to fetch user");
      const user = await response.json();
      console.log("Fetched user:", user);

      // Populate fields
      const fields = {
        username: user.userName,
        fname: user.firstName,
        lname: user.lastName,
        email: user.email,
        cellnumber: user.cellNum,
        createdDate: user.created_at
      };

      for (const [id, value] of Object.entries(fields)) {
        const el = document.getElementById(id);
        if (el) el.value = value || "";
      }

    } catch (error) {
      console.error("Error fetching user:", error);
    }
  }
  fetchUser();

  // Enable field for editing
  export function enableField(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) {
      field.disabled = false;
      field.focus();
      console.log("Enabled field:", fieldId);
    }
  }

  // Attach edit buttons
  ["Username", "Password", "Fname", "Lname", "Email", "Cell"].forEach(suffix => {
    const btn = document.getElementById(`edit${suffix}Btn`);
    if (btn) btn.addEventListener('click', () => enableField(suffix.toLowerCase()));
  });

  // Username availability check
  async function checkUsernameAvailability() {
    const username = document.getElementById('username')?.value || "";
    const email = document.getElementById('email')?.value || "";

    try {
      const response = await fetch('/api/check_user_avail', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email })
      });
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

  // Event listeners
  document.getElementById('username')?.addEventListener('input', checkUsernameAvailability);
  document.getElementById('password')?.addEventListener('input', validatePassword);

  // Update profile
  document.getElementById('updateBtn')?.addEventListener('click', async () => {
    const data = new URLSearchParams();
    ["username", "password", "fname", "lname", "email", "cellnumber"].forEach(id => {
      const el = document.getElementById(id);
      if (el) data.append(id === "username" ? "userName" : id === "cellnumber" ? "cellNum" : id, el.value);
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

      if (!response.ok) throw new Error("Failed to update user");
      alert("Profile updated successfully!");

      ["username", "password", "fname", "lname", "email", "cellnumber"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = true;
      });

    } catch (error) {
      console.error("Error updating profile:", error);
      alert("Failed to update profile. Check console.");
    }
  });
});
