// cart.js

export function getCart() {
  return JSON.parse(localStorage.getItem("checkoutCart")) || [];
}

export function clearCart() {
  localStorage.removeItem("checkoutCart");
}

export async function createPayment(payment_type, amount, reference) {
  try {
    const res = await fetch('/api/create-payment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ payment_type, amount, reference })
    });

    // Parse JSON safely
    const text = await res.text();
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = {};
    }

    clearCart();

    if (data.url) {
      window.location.href = data.url;
    } else {
      alert("Payment failed. Please try again.");
    }

  } catch {
    alert('Payment failed. Please try again.');
  }
}
