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

    if (!res.ok) throw new Error('Payment API failed');

    const data = await res.json();
    console.log('Payment created:', data);

    clearCart();
    window.location.href = data.url; // redirect to Callpay hosted page
  } catch (error) {
    console.error('Error creating payment:', error);
    alert('Payment failed. Please try again.');
  }
}
