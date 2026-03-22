// profile.js
import { requireAuth } from '/auth/authcheck.js';
import { initNavbar } from '/navbar.js';

const user = await requireAuth();

if (!user) {
  // stop execution safely
  throw new Error("Not authenticated");
}

// Load navbar
async function loadNavbar() {
  const container = document.getElementById("navbar-container");

  try {
    const response = await fetch("/navbar");
    container.innerHTML = await response.text();

    initNavbar("navbar-container");
  } catch (err) {
    console.error("Failed to load navbar:", err);
    container.innerHTML = "<p class='text-red-500'>Navbar failed to load</p>";
  }
}

loadNavbar();

const userId = user.user_id;

document.addEventListener('DOMContentLoaded', () => {

  // fetch user and populate form
  async function fetchUser() {
    try {
      const res = await fetch(`https://api.kingburger.site/users/${userId}`, {
          credentials: "include"
      });
      if (!res.ok) throw new Error("Failed to fetch user");

      const userData = (await res.json()).user || {};
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

    } catch (err) { console.error(err); }
  }
  fetchUser();

  // Enable editing fields
  function enableField(id) {
    const el = document.getElementById(id);
    if (el) el.disabled = false;
  }

  ["Username", "Password", "Fname", "Lname", "Email", "Cell"].forEach(type => {
    const btn = document.getElementById(`edit${type}Btn`);
    if (btn) btn.addEventListener('click', () => enableField(type.toLowerCase()));
  });

  // Username availability check
  document.getElementById('username')?.addEventListener('input', async () => {
    const username = document.getElementById('username')?.value || "";
    const email = document.getElementById('email')?.value || "";
    if (!username) return;
    try {
      const res = await fetch('/users/check_user_avail', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email })
      });
      const data = await res.json();
      const hint = document.getElementById('username-hint');
      if (hint) {
        hint.textContent = data.exists ? "Username already taken" : "Username is available";
        hint.style.color = data.exists ? "red" : "green";
      }
    } catch (err) { console.error(err); }
  });

  // Password validation
  document.getElementById('password')?.addEventListener('input', () => {
    const password = document.getElementById('password')?.value || "";
    const hint = document.getElementById('password-hint');
    const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{12,}$/;
    if (hint) {
      hint.textContent = regex.test(password)
        ? "Password is strong"
        : "Password must contain 1 lowercase, 1 uppercase, 1 number, 1 special character, min 12 chars";
      hint.style.color = regex.test(password) ? "green" : "red";
    }
  });

  // Update profile
  document.getElementById('updateBtn')?.addEventListener('click', async () => {
    const data = new URLSearchParams();

    const updateFields = {
      userName: document.getElementById('username')?.value,
      password: document.getElementById('password')?.value,
      firstName: document.getElementById('fname')?.value,
      lastName: document.getElementById('lname')?.value,
      email: document.getElementById('email')?.value,
      cellNum: document.getElementById('cellnumber')?.value
    };
    Object.entries(updateFields).forEach(([key, value]) => {
      if (value) data.append(key, value);
    });

    try {
      const res = await fetch(`https://api.kingburger.site/users/${userId}`, {
        method: 'PUT',
        credentials: "include",
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: data.toString()
      });
      if (!res.ok) throw new Error("Failed to update user");
      alert("Profile updated successfully!");
      ["username", "password", "fname", "lname", "email", "cellnumber"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = true;
      });
      //window.location.reload();
    } catch (err) { console.error(err); alert("Failed to update profile."); }
  });
});
