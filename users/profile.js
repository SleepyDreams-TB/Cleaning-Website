import { reqLogin } from '../navbar.js';
reqLogin();

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

    // Populate fields
    document.getElementById("username").value = user.userName || "";
    document.getElementById("fname").value = user.firstName || "";
    document.getElementById("lname").value = user.lastName || "";
    document.getElementById("email").value = user.email || "";
    document.getElementById("cellnumber").value = user.cellNum || "";
    document.getElementById("createdDate").value = user.created_at || "";

    console.log("Fetched user:", user);

  } catch (error) {
    console.error("Error fetching user:", error);
  }
}
fetchUser();

// Enable field for editing
export function enableField(fieldId) {
  const field = document.getElementById(fieldId);
  if (!field) {
    console.warn("Field not found:", fieldId);
    return;
  }
  field.disabled = false;
  field.focus();
  console.log("Enabled field:", fieldId);
}

// Attach edit buttons reliably
document.addEventListener('DOMContentLoaded', () => {
  const fields = [
    { btnId: 'editUsernameBtn', fieldId: 'username' },
    { btnId: 'editPasswordBtn', fieldId: 'password' },
    { btnId: 'editFnameBtn', fieldId: 'fname' },
    { btnId: 'editLnameBtn', fieldId: 'lname' },
    { btnId: 'editEmailBtn', fieldId: 'email' },
    { btnId: 'editCellBtn', fieldId: 'cellnumber' }
  ];

  fields.forEach(({ btnId, fieldId }) => {
    const btn = document.getElementById(btnId);
    if (btn) {
      btn.addEventListener('click', () => enableField(fieldId));
    } else {
      console.warn("Edit button not found:", btnId);
    }
  });
});

// Username availability check
async function checkUsernameAvailability() {
  const username = document.getElementById('username').value;
  const email = document.getElementById('email')?.value || "";

  try {
    const response = await fetch('/api/check_user_avail', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email })
    });
    const data = await response.json();
    const hint = document.getElementById('username-hint');
    if (data.exists) {
      hint.textContent = "Username already taken";
      hint.style.color = "red";
    } else {
      hint.textContent = "Username is available";
      hint.style.color = "green";
    }
  } catch (error) {
    console.error("Error checking username:", error);
  }
}

// Password validation
function validatePassword() {
  const password = document.getElementById('password').value;
  const hint = document.getElementById('password-hint');
  const regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{12,}$/;

  if (regex.test(password)) {
    hint.textContent = "Password is strong";
    hint.style.color = "green";
  } else {
    hint.textContent = "Password must contain 1 lowercase, 1 uppercase, 1 number, 1 special character, min 12 chars";
    hint.style.color = "red";
  }
}

// Event listeners for username and password
document.getElementById('username')?.addEventListener('input', checkUsernameAvailability);
document.getElementById('password')?.addEventListener('input', validatePassword);

// Update profile
document.getElementById('updateBtn')?.addEventListener('click', async () => {
  const data = new URLSearchParams();
  data.append("userName", document.getElementById("username").value);
  data.append("password", document.getElementById("password").value);
  data.append("firstName", document.getElementById("fname").value);
  data.append("lastName", document.getElementById("lname").value);
  data.append("email", document.getElementById("email").value);
  data.append("cellNum", document.getElementById("cellnumber").value);

  console.log("Sending update request with:", Object.fromEntries(data));

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

    const updatedUser = await response.json();
    console.log("Update response:", updatedUser);
    alert("Profile updated successfully!");

    ["username", "password", "fname", "lname", "email", "cellnumber"].forEach(id => {
      document.getElementById(id).disabled = true;
    });

  } catch (error) {
    console.error("Error updating profile:", error);
    alert("Failed to update profile. Check console.");
  }
});
