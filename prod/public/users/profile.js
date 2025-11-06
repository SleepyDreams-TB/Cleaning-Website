// profile.js
document.addEventListener('DOMContentLoaded', () => {
  const JWT = localStorage.getItem("jwt");
  if (!JWT) return window.location.href = "../index.html";

  let userId;
  try {
    const payload = jwt_decode(JWT);
    userId = payload.user_id;
  } catch {
    return window.location.href = "../index.html";
  }

  // apiFetch user and populate form
  async function apiFetchUser() {
    try {
      const res = await apiFetch(`https://api.kingburger.site/users/${userId}`, {
        headers: { 'Authorization': `Bearer ${JWT}` }
      });
      if (!res.ok) throw new Error("Failed to apiFetch user");

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
  apiFetchUser();

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
      const res = await apiFetch('/api/check_user_avail', {
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
    ["username", "password", "fname", "lname", "email", "cellnumber"].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        const key = id === "username" ? "userName" : id === "cellnumber" ? "cellNum" : id;
        data.append(key, el.value || "");
      }
    });

    try {
      const res = await apiFetch(`https://api.kingburger.site/users/update/${userId}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${JWT}`, 'Content-Type': 'application/x-www-form-urlencoded' },
        body: data.toString()
      });
      if (!res.ok) throw new Error("Failed to update user");
      alert("Profile updated successfully!");
      ["username", "password", "fname", "lname", "email", "cellnumber"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = true;
      });
      window.location.reload();
    } catch (err) { console.error(err); alert("Failed to update profile."); }
  });
});
