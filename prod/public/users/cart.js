//cart.js
// ----- Notification Helper -----
export function notifyUser(message) {
  alert(message);
  console.log("User notification:", message);
}

// ----- Cart storage & management -----
export function getCart() {
  try {
    return JSON.parse(localStorage.getItem("checkoutCart")) || [];
  } catch (err) {
    console.error("Failed to parse checkoutCart:", err);
    return [];
  }
}

export function saveCart(cart) {
  try {
    localStorage.setItem("checkoutCart", JSON.stringify(cart));
  } catch (err) {
    console.error("Failed to save cart:", err);
  }
}

export function addToCart(product) {
  const cart = getCart();
  // Use _id if it exists, otherwise use id
  const itemId = product._id || product.id;
  const existingItem = cart.find(item => (item._id || item.id) === itemId);

  if (existingItem) {
    existingItem.quantity += 1;
  } else {
    cart.push({ ...product, quantity: 1 });
  }

  saveCart(cart);
}

export function clearCart() {
  localStorage.removeItem("checkoutCart");
  console.log("Cart cleared");
}

export function deleteCartItem(id) {
  let cart = getCart();
  const initialLength = cart.length;
  cart = cart.filter(item => (item._id || item.id) !== id);
  saveCart(cart);
  console.log(`Deleted item ${id} from cart. Removed ${initialLength - cart.length} items.`);
  return cart;
}

export function recalcTotal(cart) {
  return cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// ----- Fetch Billing Info -----
export async function getBillingInfoAddress() {
  try {
    const res = await fetch("https://api.kingburger.site/users/dashboard/info", {
      credentials: "include"
    });

    if (!res.ok) {
      if (res.status === 401) {
        notifyUser("Your session has expired. Please log in again.");
        window.location.href = "/login";
        return null;
      }
      throw new Error("Failed to fetch billing info");
    }

    const data = await res.json();
    const billing_address = data.billing_address;

    if (!billing_address) {
      notifyUser('No billing information found. Please add a billing address in the "Billing Section".');
      return null;
    }

    return billing_address;
  } catch (err) {
    console.error("Failed to fetch billing info:", err);
    return null;
  }
}
