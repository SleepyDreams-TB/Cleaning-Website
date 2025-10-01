export function getCart() {
  return JSON.parse(localStorage.getItem("checkoutCart")) || [];
}

export function saveCart(cart) {
  localStorage.setItem("checkoutCart", JSON.stringify(cart));
}

export function addToCart(product) {
  const cart = getCart();
  const existingItem = cart.find(item => item._id === product._id);

  if (existingItem) {
    existingItem.quantity += 1;
  } else {
    cart.push({ ...product, quantity: 1 });
  }

  saveCart(cart);
  alert(`${product.name} added to cart!`);
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

    const text = await res.text();
    console.log("Raw response from backend:", text);

    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch (err) {
      console.warn("Failed to parse JSON, using raw text instead.");
      data = { raw_response: text };
    }

    console.log('Payment created:', data);

    clearCart();

    // Redirect if URL exists
    if (data.url) {
      window.location.href = data.url;
    } else if (data.raw_response) {
      // Optional: parse URL from raw text if backend returned it as string
      const urlMatch = data.raw_response.match(/https?:\/\/\S+/);
      if (urlMatch) {
        window.location.href = urlMatch[0];
      } else {
        alert("Payment failed or no URL returned. Check console for raw response.");
      }
    } else {
      alert("Payment failed. Check console for details.");
    }

  } catch (error) {
    console.error('Error creating payment:', error);
    alert('Payment failed. Please try again.');
  }
}


