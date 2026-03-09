//processhelpers.js
import { getCart, clearCart, notifyUser, getBillingInfoAddress } from "../users/cart.js";

// ----- Generate Unique Merchant Reference -----
function generateMerchantReference() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  const suffix = Array.from({ length: 3 }, () => chars[Math.floor(Math.random() * chars.length)]).join('');
  const now = new Date();
  const timestamp = now.toISOString().replace(/[-:T]/g, '').slice(0, 12);
  return `PAY-${timestamp}-${suffix}`;
}

function getEndpoint(type) {
  switch (type) {
    case "eft": return "https://api.kingburger.site/api/create-payment/eft";
    case "credit_card": return "https://api.kingburger.site/api/create-payment/credit-card";
    case "saved_card": return "https://api.kingburger.site/api/create-payment/saved-card";
    case "tokenize_card": return "https://api.kingburger.site/api/tokenize-card";
    default: throw new Error("Unknown payment type");
  }
}

// ----- Create Order in Backend -----
async function createBackendOrder(payment_type, merchant_reference, addressType) {
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
        merchant_reference,
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



// ----- Tokenize Card Data with Callpay -----
export async function tokenizeCardData(merchant_reference, cardData) {
  try {
    const bodyData = {
      merchant_reference,
      cardNumber: cardData.pan,
      cardHolderName: cardData.cardHolderName,
      expiryDate: cardData.expiry,
      cvv: cardData.cvv,
      saveCardBool: false,
      user_id: cardData.user_id
    };

    const res = await fetch(getEndpoint("tokenize_card"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(bodyData)
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    if (data?.status === "success" && data?.response?.guid) {
      return data.response.guid;
    } else {
      console.error("Card tokenization failed:", data);
      notifyUser("Card details are invalid. Please check and try again.");
      return null;
    }

  } catch (err) {
  console.error("Card tokenization error:", err);
  console.error("Error name:", err.name);
  console.error("Error message:", err.message);
  console.error("cardData received:", cardData);
  notifyUser("Something went wrong while processing your card. Please try again.");
  return null;
}
}


// ----- Create Payment -----
export async function createPayment(payment_type, amount, deliveryAddress, saveCardBool, dataObject) {
  const merchant_reference = generateMerchantReference();

  if (saveCardBool) {
    try {
      const token = await tokenizeCardData(merchant_reference, dataObject);
    }
    catch (err) {
      console.error("Error tokenizing card for saving:", err);
      notifyUser("Could not save card details. Please check your information and try again.");
      return;
    }
  }
  const orderData = await createBackendOrder(payment_type, merchant_reference, deliveryAddress);
  if (!orderData?.success) {
    console.log("Order creation failed)");
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
    cardDataset: {
      cardNumber: dataObject.pan,
      expiryDate: dataObject.expiry,
      cvv: dataObject.cvv,
      cardHolderName: dataObject.cardHolderName,
      saveCardBool: false,
      user_id: dataObject.user_id
    }
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
    const res = await fetch(getEndpoint(payment_type), {
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