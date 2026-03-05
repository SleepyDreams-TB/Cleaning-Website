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
  notifyUser(`${product.name} added to cart!`);
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
export async function getBillingInfoAddress(token) {

  if (!token) {
    notifyUser("Please log in");
    return null;
  }
  try {
    const res = await fetch("https://api.kingburger.site/users/dashboard/info", {
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Invalid token");
    const data = await res.json();
    const billing_address = data.billing_address

    if (!billing_address) {
      notifyUser('No billing information found. Please add a billing address in the "Billing Section".');
      return null;
    }

    return billing_address
  } catch (err) {
    console.error("Failed to fetch billing info:", err);
    notifyUser("Could not fetch billing info. Please try again.");
    return null;
  }
}

// ----- Create Order in Backend -----
export async function createBackendOrder(payment_type, addressType) {
  const cart = getCart();
  console.log("Current cart:", cart);

  if (cart.length === 0) {
    notifyUser("Your cart is empty.");
    return null;
  }

  const token = localStorage.getItem("jwt");
  console.log("Token:", token);

  if (!token) {
    notifyUser("Please log in before placing an order.");
    return null;
  }

  try {
    const addresses = await getBillingInfoAddress(token);
    if (!addresses) return null;

    const deliveryAddress = addresses[addressType];

    if (!deliveryAddress) {
      notifyUser("Invalid delivery address selected.");
      return null;
    }

    const res = await fetch("https://api.kingburger.site/api/orders", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
      },
      body: JSON.stringify({
        payment_type,
        items: cart,
        delivery_info: {
          type: addressType,
          street: deliveryAddress.street,
          city: deliveryAddress.city,
          suburb: deliveryAddress.suburb,
          postal_code: deliveryAddress.postal_code,
          country: deliveryAddress.country
        }
      })
    });

    const data = await res.json();
    console.log("Order creation response:", data);

    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    return data;
  } catch (err) {
    console.error("Failed to create backend order:", err);
    notifyUser("We could not create your order. Please try again.");
    return null;
  }
}