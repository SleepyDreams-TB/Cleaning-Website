export function addToCart(product) {
  // Get existing cart from localStorage or start a new one
  const checkoutCart = JSON.parse(localStorage.getItem("checkoutCart")) || [];

  // Check if product already exists in cart
  const existing = checkoutCart.find(item => item._id === product._id);
  if (existing) {
    existing.quantity += 1;  // Increase quantity if already in cart
  } else {
    checkoutCart.push({ ...product, quantity: 1 });  // Add new product
  }

  // Save cart back to localStorage
  localStorage.setItem("checkoutCart", JSON.stringify(checkoutCart));

  alert(`${product.name} added to cart!`);
}
