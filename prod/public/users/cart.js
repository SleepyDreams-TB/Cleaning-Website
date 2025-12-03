// ----- Notification Helper -----
import { apiFetch } from '/utils.js';

function notifyUser(message) {
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
  // Match against both _id and id for flexibility
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
    const billing_info = data.billing_info

    if (!billing_info || !billing_info.billing_addresses) {
      notifyUser('No billing information found. Please add a billing address in the "Billing Section".');
      return null;
    }

    const addresses = billing_info.billing_addresses;
    return addresses
  } catch (err) {
    console.error("Failed to fetch billing info:", err);
    notifyUser("Could not fetch billing info. Please try again.");
    return null;
  }
}

// ----- Create Order in Backend -----
export async function createBackendOrder(payment_type) {
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
    const deliveryAddress = addresses[addressType];

    if (!deliveryAddress) {
      notifyUser("Invalid delivery address selected.");
      return null;
    }

    const res = await apiFetch("https://api.kingburger.site/api/orders", {
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

    return data;
  } catch (err) {
    console.error("Failed to create backend order:", err);
    notifyUser("We could not create your order. Please try again.");
    return null;
  }
}

// ----- Create Payment -----
export async function createPayment(payment_type, amount, deliveryAddress) {
  try {
    const orderData = await createBackendOrder(payment_type, deliveryAddress);
    if (!orderData || !orderData.merchant_reference) {
      notifyUser("We could not create your order. Please try again.");
      return;
    }

    console.log("Creating payment for merchant_reference:", orderData.merchant_reference);

    const res = await apiFetch("https://api.kingburger.site/api/create-payment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        payment_type,
        amount,
        merchant_reference: orderData.merchant_reference
      })
    });

    const text = await res.text();
    let data = {};
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      console.warn("Failed to parse payment response as JSON, using raw text.");
      data = { raw_response: text };
    }

    console.log("Payment response data:", data);

    clearCart();

    if (data && data.response) {
      const response = data.response;
      console.log("Payment response object:", response);

      if (response.url) {
        console.log("Redirecting to payment URL:", response.url);
        window.location.href = response.url;
      } else if (response.raw_response) {
        console.log("Raw response received:", response.raw_response);
        const urlMatch = response.raw_response.match(/https?:\/\/\S+/);
        if (urlMatch) {
          console.log("Extracted URL from raw response:", urlMatch[0]);
          window.location.href = urlMatch[0];
        } else {
          console.error("No URL found in raw_response");
          notifyUser("Something went wrong. Please try again.");
        }
      } else {
        console.error("Response object does not contain url or raw_response");
        notifyUser("Something went wrong. Please try again.");
      }
    } else {
      console.error("Data or data.response is undefined or null", data);
      notifyUser("Something went wrong. Please try again.");
    }
  } catch (error) {
    console.error("Error during payment creation:", error);
    notifyUser("Something went wrong. Please try again.");
  }
}