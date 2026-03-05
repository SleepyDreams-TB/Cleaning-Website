//processhelpers.js
import { getCart, clearCart, notifyUser, getBillingInfoAddress } from "../users/cart.js";

// ----- Create Order in Backend -----
export async function createBackendOrder(payment_type, addressType) {
  const cart = getCart();
  console.log("Current cart:", cart);

  if (cart.length === 0) {
    notifyUser("Your cart is empty.");
    return null;
  }

  const token = localStorage.getItem("jwt");
  if (!token) {
    notifyUser("Please log in before placing an order.");
    return null;
  }

  try {
    const addresses = await getBillingInfoAddress(token);
    if (!addresses) return null; // notifyUser already called inside getBillingInfoAddress

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

    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    console.log("Order creation response:", data);
    return data;
  } catch (err) {
    console.error("Failed to create backend order:", err);
    notifyUser("We could not create your order. Please try again.");
    return null;
  }
}

// ----- Create Payment -----
const ENDPOINTS = {
  eft: "https://api.kingburger.site/api/create-payment/eft",
  credit_card: "https://api.kingburger.site/api/create-payment/credit-card",
  saved_card: "https://api.kingburger.site/api/create-payment/saved-card"
};

export async function createPayment(payment_type, amount, deliveryAddress, dataObject) {
  const orderData = await createBackendOrder(payment_type, deliveryAddress);
  if (!orderData?.merchant_reference) {
    notifyUser("We could not create your order. Please try again.");
    return;
  }

  // ----- Build request body -----
  let bodyData = {};
  if (payment_type === "eft") {
    if (!dataObject?.customer_bank) {
      notifyUser("Please select a bank for EFT payment.");
      return;
    }
    bodyData = {
      amount,
      merchant_reference: orderData.merchant_reference,
      customer_bank: dataObject.customer_bank
    };
  } else if (payment_type === "credit_card") {
    bodyData = {
      amount,
      merchant_reference: orderData.merchant_reference,
      cardDataset: dataObject
    };
  } else if (payment_type === "saved_card") {
    if (!dataObject?.guid) {
      notifyUser("No saved card found. Please use a new card.");
      return;
    }
    bodyData = {
      amount,
      merchant_reference: orderData.merchant_reference,
      guid: dataObject.guid
    };
  } else {
    notifyUser("Unknown payment type.");
    return;
  }

  // ----- Send to backend & handle response -----
  try {
    const res = await fetch(ENDPOINTS[payment_type], {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(bodyData)
    });

    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    const inner = data.response; // Callpay payload unwrapped from { status, response }

    if (!inner) {
      notifyUser("Something went wrong. Please try again.");
      return;
    }

    if (payment_type === "eft") {
      // inner = { key, url, origin }
      if (inner.url) {
        clearCart();
        window.location.href = inner.url;
      } else {
        notifyUser("Could not initiate EFT payment. Please try again.");
      }

    } else if (payment_type === "credit_card") {
      // inner = { type: "result", transaction: { status, ... } }
      //      OR { type: "3ds_redirect", redirect_url, gateway_transaction_id }
      clearCart();
      if (inner.type === "3ds_redirect") {
        window.location.href = inner.redirect_url;
      } else if (inner.type === "result") {
        if (inner.transaction?.status === "complete") {
          window.location.href = "/redirects/success";
        } else {
          notifyUser(`Payment failed: ${inner.transaction?.reason || inner.transaction?.status}`);
        }
      } else {
        notifyUser("Unexpected response from payment provider.");
      }

    } else if (payment_type === "saved_card") {
      // inner = { success: 1, amount, reason, callpay_transaction_id, ... }
      clearCart();
      if (inner.success === 1) {
        window.location.href = "/redirects/success";
      } else {
        notifyUser(`Payment failed: ${inner.reason || "Unknown error"}`);
      }
    }

  } catch (err) {
    console.error("Payment error:", err);
    notifyUser("Something went wrong. Please try again.");
  }
}