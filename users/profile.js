import { reqLogin } from '../navbar.js';
reqLogin();

// Global variables
let userId;
const JWT = localStorage.getItem("jwt");
if (!JWT) window.location.href = "../index.html";

// Decode JWT and log
try {
  const payload = jwt_decode(JWT);
  console.log("Decoded JWT payload:", payload);
  userId = payload.user_id;
  console.log("userId used in fetch:", userId);
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
        'Authorization': `Bearer ${JWT}`,
        'Content-Type': 'application/json'
      }
    });
    if (!response.ok) throw new Error("Failed to fetch user");
    const user = await response.json();

    // Populate fields (match MongoDB field names)
    document.getElementById("username").value = user.userName || "";
    document.getElementById("fname").value = user.firstName || "";
    document.getElementById("lname").value = user.lastName || "";
    document.getElementById("email").value = user.email || "";
    document.getElementById("cellnumber").value = user.cellNum || "";
    document.getElementById("createdDate").value = user.created_at || "";

  } catch (error) {
    console.error("Error fetching user:", error);
  }
}
fetchUser();

// Enable field for editing
export function enableField(fieldId) {
  const field = document.getElementById(fieldId);
  field.disabled = false;
  field.focus();
}

// Validate username availability
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

// Validate password strength
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

// Event listeners
document.getElementById('username').addEventListener('input', checkUsernameAvailability);
document.getElementById('password').addEventListener('input', validatePassword);

// Update profile
document.getElementById('updateBtn').addEventListener('click', async () => {
  try {
    const response = await fetch(`https://api.kingburger.site/users/update/${userId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${JWT}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        userName: document.getElementById("username").value,
        password: document.getElementById("password").value,
        firstName: document.getElementById("fname").value,
        lastName: document.getElementById("lname").value,
        email: document.getElementById("email").value,
        cellNum: document.getElementById("cellnumber").value
      })
    });

    if (!response.ok) throw new Error("Failed to update user");
    alert("Profile updated successfully!");

    // Disable fields again after update
    ["username", "password", "fname", "lname", "email", "cellnumber"].forEach(id => {
      document.getElementById(id).disabled = true;
    });

  } catch (error) {
    console.error("Error updating profile:", error);
    alert("Failed to update profile. Check console.");
  }
});
