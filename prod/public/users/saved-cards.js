import { getCardDetails, tokenizeCardData } from '/payment_process/processhelpers.js';

document.addEventListener("DOMContentLoaded", async () => {
  const jwt = localStorage.getItem("jwt");

  if (!jwt) {
    window.location.href = "/redirects/401";
    return;
  }

  const cardsList = document.getElementById("cardsList");
  const addCardBtn = document.getElementById("addCardBtn");
  const addCardForm = document.getElementById("addCardForm");

  // ─── Message Helper ────────────────────────────────────────────────────────

  function showMessage(type, message) {
    const box = document.getElementById("message");
    const icon = document.getElementById("messageIcon");
    const text = document.getElementById("messageText");
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

  // ─── Render Card ──────────────────────────────────────────────────────────

  function renderCards(card) {
    if (!card || !card.lastFour) {
      cardsList.innerHTML = `
        <p class="text-gray-400 text-sm text-center py-4">No saved card yet. Add one below.</p>
      `;
      return;
    }

    cardsList.innerHTML = `
      <div class="card-row">
        <div class="card-row-info">
          <div class="card-icon">
            <i class="fas fa-credit-card"></i>
          </div>
          <div>
            <div class="card-digits">•••• •••• •••• ${card.lastFour}</div>
            <div class="card-expiry">Expires ${card.expiryDate}</div>
            <div class="card-scheme">${card.cardScheme}</div>
          </div>
        </div>
      </div>
    `;
  }

  // ─── Load Card ─────────────────────────────────────────────────────────────

  async function loadCards() {
    const result = await getCardDetails(jwt);

    if (!result) {
      cardsList.innerHTML = `<p class="text-gray-400 text-sm text-center py-4">Failed to load card.</p>`;
      showMessage("error", "Failed to load saved card.");
      return;
    }

    renderCards(result);
  }

  // ─── Auto-format inputs ────────────────────────────────────────────────────

  document.getElementById("cardNumber").addEventListener("input", (e) => {
    let val = e.target.value.replace(/\D/g, "").substring(0, 16);
    e.target.value = val.replace(/(.{4})/g, "$1 ").trim();
  });

  document.getElementById("expiryDate").addEventListener("input", (e) => {
    let val = e.target.value.replace(/\D/g, "").substring(0, 4);
    if (val.length >= 3) val = val.substring(0, 2) + "/" + val.substring(2);
    e.target.value = val;
  });

  // ─── Add Card Submit ───────────────────────────────────────────────────────

  addCardForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    addCardBtn.disabled = true;
    addCardBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Processing...`;

    const merchant_reference = `CARD-${Date.now()}`;

    const cardData = {
      pan: document.getElementById("cardNumber").value.replace(/\s/g, ""),
      cardHolderName: document.getElementById("cardHolderName").value.trim(),
      expiry: document.getElementById("expiryDate").value.trim(),
      cvv: document.getElementById("cvv").value.trim(),
      user_id: null,
    };

    try {
      const guid = await tokenizeCardData(merchant_reference, cardData);

      if (guid) {
        showMessage("success", "Card added successfully.");
        addCardForm.reset();
        await loadCards();
      } else {
        showMessage("error", "Failed to add card. Please check your details.");
      }
    } finally {
      addCardBtn.disabled = false;
      addCardBtn.innerHTML = `<i class="fas fa-plus"></i> Add Card`;
    }
  });

  // ─── Init ──────────────────────────────────────────────────────────────────

  await loadCards();
});