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
  cart = cart.filter(item => item.id !== id);
  saveCart(cart);
  return cart;
}

export function recalcTotal(cart) {
  return cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// ----- Create Order in Backend -----
export async function createBackendOrder(payment_type) {
  const cart = getCart();
  if (cart.length === 0) {
    alert("Your cart is empty.");
    return null;
  }

  const token = localStorage.getItem("jwt");
  console.log("Token:", token);

  if (!token) {
    alert("Please log in before placing an order.");
    return null;
  }

  try {
    const res = await fetch("https://api.kingburger.site/api/orders", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
      },
      body: JSON.stringify({
        payment_type: payment_type,
        items: cart
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error();

    return data;
  } catch {
    alert("We could not create your order. Please try again.");
    return null;
  }
}

// ----- Create Payment -----
export async function createPayment(payment_type, amount) {
  try {
    const orderData = await createBackendOrder(payment_type);
    if (!orderData || !orderData.merchant_reference) {
      alert("We could not create your order. Please try again.");
      return;
    }

    const res = await fetch("https://api.kingburger.site/api/create-payment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        payment_type: payment_type,
        amount: amount,
        merchant_reference: orderData.merchant_reference
      })
    });

    const text = await res.text();
    let data = {};
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = { raw_response: text };
    }

    clearCart();

    if (data && data.response) {
      const response = data.response;
      if (response.url) {
        window.location.href = response.url;
      } else if (response.raw_response) {
        const urlMatch = response.raw_response.match(/https?:\/\/\S+/);
        if (urlMatch) {
          window.location.href = urlMatch[0];
        } else {
          alert("Something went wrong. Please try again.");
        }
      } else {
        alert("Something went wrong. Please try again.");
      }
    } else {
      alert("Something went wrong. Please try again.");
    }
  } catch {
    alert("Something went wrong. Please try again.");
  }
}
