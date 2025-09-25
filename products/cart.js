import crypto from 'crypto';

const salt = 'your_salt_here'; // Replace with your actual salt
const Orgid = 'your_org_id_here'; // Replace with your actual Org ID

export function addToCart(product) {
  // Get existing cart from localStorage or start a new one
  const checkoutCart = JSON.parse(localStorage.getItem("checkoutCart")) || [];

  // Check if product already exists in cart
  const existing = checkoutCart.find(item => item._id === product._id);
  if (existing) {
    existing.quantity += 1;  // Increase quantity if already in cart
  } else {
    checkoutCart.push({
      _id: product._id,
      name: product.name,
      price: product.price,
      image_url: product.image_url
      , quantity: 1
    });  // Add new product
  }

  // Save cart back to localStorage
  localStorage.setItem("checkoutCart", JSON.stringify(checkoutCart));
  console.log("Cart updated:", checkoutCart);
  alert(`${product.name} added to cart!`);

}

export function getCart() {
  return JSON.parse(localStorage.getItem("checkoutCart")) || [];
}

export function clearCart() {
  localStorage.removeItem("checkoutCart");
  console.log("Cart cleared");
}

export function createPayment(payment_type, amount, reference) {

  fetch('https://services.callpay.com/api/v2/payment-key', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Auth-Token': Token,
      'Org-id': Orgid,
      'Timestamp': new Date().toISOString()
    },
    body: JSON.stringify({
      payment_type,
      amount,
      reference
    })
  })
    .then(response => response.json())
    .then(data => {
      console.log('Payment created:', data);
      alert('Payment successful! Reference: ' + data.reference);
      clearCart(); // Clear cart after successful payment
      window.location.href = '/products/cart.html'; // Redirect to cart page
    })
    .catch(error => {
      console.error('Error creating payment:', error);
      alert('Payment failed. Please try again.');
    });
}