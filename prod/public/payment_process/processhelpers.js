//processhelpers.js
import { getCart, clearCart, notifyUser, getBillingInfoAddress } from "../users/cart.js";
import { requireAuth } from '/auth/authcheck.js';

const user = await requireAuth();
if (!user) window.location.href = "/login";

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
    case "get-card": return "https://api.kingburger.site/api/get-card";
    case "paypal": return "/api/paypal/create-order";
    default: throw new Error("Unknown payment type");
  }
}

// ----- Bin Lookup function
export function lookupBin(bin) {
  return fetch(`/api/bin/${bin}`)
    .then(res => {
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return res.json();
    })
    .then(data => {
      const binData = data.data
      const scheme = binData.brand;
      return scheme;
    })
    .catch(err => {
      console.error("BIN lookup failed:", err.message);
      return null;
    });
}

export async function getCardDetails() {
  try {
    const res = await fetch(getEndpoint("get-card"), {
      method: "GET",
      credentials: "include",
      headers: { "Content-Type": "application/json" }
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("Failed to get card details:", err);
    return null;
  }
}

// ----- Create Order in Backend -----
async function createBackendOrder(payment_type, merchant_reference, addressType) {
  const cart = getCart();

  try {
    const addresses = await getBillingInfoAddress();
    if (!addresses) return null;

    const deliveryAddress = addresses[addressType];
    if (!deliveryAddress) {
      notifyUser("Invalid delivery address selected.");
      return null;
    }

    const res = await fetch("https://api.kingburger.site/api/orders", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json"
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

    if (!res.ok) {
      if (res.status === 401) {
        notifyUser("Your session has expired. Please log in again.");
        window.location.href = "/login";
        return null;
      }
      throw new Error(`HTTP error ${res.status}`);
    }
    const data = await res.json();
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
      cardScheme: cardData.cardScheme
    };

    const res = await fetch(getEndpoint("tokenize_card"), {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json"
      },
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
    notifyUser("Something went wrong while processing your card. Please try again.");
    return null;
  }
}

// ----- Create Paypal Payment -----
export async function createPaypalPayment(deliveryAddress) {
  const merchant_reference = generateMerchantReference();

  const bodyData = {
    merchant_reference: merchant_reference
  };

  const orderData = await createBackendOrder("paypal", merchant_reference, deliveryAddress);
  if (!orderData?.success) {
    return;
  }
  try {
    const res = await fetch(getEndpoint("paypal"), {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(bodyData)
    });

    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    const approve_url = data.approve_url;

    if (approve_url) {
      clearCart();
      localStorage.setItem("merchant_reference", merchant_reference);
      window.location.href = approve_url;
    } else {
      notifyUser("Could not initiate PayPal payment. Please try again.");
    }
  } catch (err) {
    console.error("Payment error:", err);
    notifyUser("Something went wrong. Please try again.");
  }
}

// ----- Create Payment -----
export async function createPayment(payment_type, deliveryAddress, saveCardBool, dataObject) {
  const merchant_reference = generateMerchantReference();

  if (saveCardBool) {
    await tokenizeCardData(merchant_reference, dataObject);
  }
  const orderData = await createBackendOrder(payment_type, merchant_reference, deliveryAddress);
  if (!orderData?.success) {
    return;
  }
  const verifiedAmount = orderData.calculated_amount;

  // ----- Build request body -----
  let bodyData = {};
  if (payment_type === "eft") {
    if (!dataObject?.customer_bank) {
      notifyUser("Please select a bank for EFT payment.");
      return;
    }
    bodyData = {
      amount: verifiedAmount,
      merchant_reference: merchant_reference,
      customer_bank: dataObject.customer_bank
    };
  } else if (payment_type === "credit_card") {
    bodyData = {
      amount: verifiedAmount,
      merchant_reference: merchant_reference,
      cardDataset: {
        cardNumber: dataObject.pan,
        expiryDate: dataObject.expiry,
        cvv: dataObject.cvv,
        cardHolderName: dataObject.cardHolderName,
        cardScheme: dataObject.cardScheme
      }
    };
  } else if (payment_type === "saved_card") {
    if (!dataObject?.guid) {
      notifyUser("No saved card found. Please use a new card.");
      return;
    }
    bodyData = {
      amount: verifiedAmount,
      merchant_reference: merchant_reference,
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
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(bodyData)
    });

    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();
    const inner = data.response; // Callpay payload unwrapped from { status, response }
    console.log('Payment response:', inner);

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

      if (inner.type === "3ds_redirect") {
        window.location.href = inner.redirect_url;
      } else if (inner.type === "result") {
        if (inner.status === "complete") {
          window.location.href = "/redirects/success";
        } else {
          notifyUser(`Payment failed: ${inner.transaction?.reason || inner.transaction?.status}`);
        }
      } else {
        notifyUser("Unexpected response from payment provider.");
      }

    } else if (payment_type === "saved_card") {
      // inner = { success: 1, amount, reason, callpay_transaction_id, ... }
      if (inner.type === "3ds_redirect") {
        clearCart();
        window.location.href = inner.redirect_url;
      } else if (inner.type === "result") {
        if (inner.transaction?.status === "complete") {
          clearCart();
          window.location.href = "/redirects/success";
        } else {
          notifyUser(`Payment failed: ${inner.reason || "Unknown error"}`);
        }
      } else {
        notifyUser("Unexpected response from payment provider.");
      }

    }
  } catch (err) {
    console.error("Payment error:", err);
    notifyUser("Something went wrong. Please try again.");
  }
}