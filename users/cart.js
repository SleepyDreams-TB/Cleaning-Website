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

export function deleteCartItem(id) {
  let cart = getCart();
  cart = cart.filter(item => item._id !== id);
  saveCart(cart);
  return cart;
}

export function recalcTotal(cart) {
  return cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// ----- Create Order -----
export async function createOrder(orderData) {
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

    return data;

  } catch (err) {
    console.error("Order creation error:", err);
    throw err;
  }
}

// ----- Payment -----
export async function createPayment(payment_type, amount) {

  const orderData = {
    user_id: localStorage.getItem("userId") || null,
    items: getCart(),
    merchant_reference: '',
    total: amount,
    payment_type: payment_type
  };

  const response = await createOrder(orderData);

  if (response && !response.error) {
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = { raw_response: text };
    }

      const text = await res.text();
      let data;
      try {
        data = text ? JSON.parse(text) : {};
      } catch {
        data = { raw_response: text };
      }

      clearCart();
      try {
        if (data.url) {
          window.location.href = data.url;
        } else if (data.raw_response) {
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
  } else {
    alert("Order creation failed. Please try again.");
  }
}
