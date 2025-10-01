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

    // Read the response as text first
    const text = await res.text();
    console.log("Raw response from backend:", text);

    // Safely parse JSON
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch (err) {
      console.error("Failed to parse JSON:", err);
      data = { raw_response: text };
    }

    console.log('Payment created:', data);

    clearCart(); // your existing function

    // Redirect only if Callpay returned a URL
    if (data.url) {
      window.location.href = data.url;
    } else {
      alert("Payment failed or no URL returned. Check console for raw response.");
    }

  } catch (error) {
    console.error('Error creating payment:', error);
    alert('Payment failed. Please try again.');
  }
}
