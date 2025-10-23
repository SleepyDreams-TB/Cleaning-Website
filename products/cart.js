// ----- Cart storage & management -----
export function getCart() {
  return JSON.parse(localStorage.getItem("checkoutCart")) || [];
}

export function saveCart(cart) {
  localStorage.setItem("checkoutCart", JSON.stringify(cart));
}

export function addToCart(product) {
  const cart = getCart();
  const existingItem = cart.find(item => item._id === product._id);

  if (existingItem) existingItem.quantity += 1;
  else cart.push({ ...product, quantity: 1 });

  saveCart(cart);
  alert(`${product.name} added to cart!`);
}

export function clearCart() {
  localStorage.removeItem("checkoutCart");
}

// Delete single item by _id
export function deleteCartItem(id) {
  let cart = getCart();
  cart = cart.filter(item => item._id !== id);
  saveCart(cart);
  return cart;
}

// Recalculate total price
export function recalcTotal(cart) {
  return cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// ----- Payment -----
export async function createPayment(payment_type) {
  const cartItems = getCart();
  if (!cartItems.length) {
    alert("Your cart is empty!");
    return;
  }

  const totalAmount = recalcTotal(cartItems).toFixed(2);

  // Call backend payment endpoint directly
  try {
    const res = await fetch('https://api.kingburger.site/api/create-payment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        payment_type,
        amount: totalAmount,
        user_id: localStorage.getItem("userId") || null,
        items: cartItems // backend will handle order creation and merchant_reference
      })
    });

    const text = await res.text();
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = { raw_response: text };
    }

    // Clear cart after initiating payment
    clearCart();

    if (data.url) {
      // Redirect to payment page
      window.location.href = data.url;
    } else if (data.raw_response) {
      // Try to extract a URL from raw response
      const urlMatch = data.raw_response.match(/https?:\/\/\S+/);
      if (urlMatch) window.location.href = urlMatch[0];
      else alert("Payment failed. Check console for raw response.");
    } else {
      alert("Payment failed. Check console for details.");
    }

  } catch (err) {
    console.error("Payment error:", err);
    alert("Payment failed. Please try again.");
  }
}
