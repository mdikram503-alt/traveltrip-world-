const params = new URLSearchParams(location.search);
const packageCode = params.get("code") || "";
const planName = params.get("name") || "Travel eSIM";
const shownPrice = params.get("price") || "";
const status = document.getElementById("status");
document.getElementById("plan-name").textContent = planName;
document.getElementById("plan-meta").textContent = [params.get("data"), params.get("validity"), params.get("location")].filter(Boolean).join(" · ");
document.getElementById("total").textContent = shownPrice ? `$${shownPrice} USD` : "Verified at checkout";
document.getElementById("back").href = `/pages/plans.html?cc=${encodeURIComponent(params.get("cc") || "AE")}`;

function message(text, type = "") {
  status.className = `status ${type}`.trim();
  status.textContent = text;
}

function customer() {
  const buyerName = document.getElementById("name").value.trim();
  const buyerEmail = document.getElementById("email").value.trim();
  if (!buyerName) throw new Error("Enter your full name.");
  if (!/^\S+@\S+\.\S+$/.test(buyerEmail)) throw new Error("Enter a valid email for QR delivery.");
  if (!packageCode) throw new Error("This package link is invalid. Please choose the plan again.");
  return { buyerName, buyerEmail };
}

async function json(url, options) {
  const response = await fetch(url, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || "Checkout could not continue.");
  return body;
}

try {
  const config = await json("/api/checkout/paypal/config");
  const script = document.createElement("script");
  script.src = `https://www.paypal.com/sdk/js?client-id=${encodeURIComponent(config.clientId)}&currency=${encodeURIComponent(config.currency)}&intent=capture`;
  script.onload = () => {
    window.paypal.Buttons({
      style: { layout: "vertical", shape: "rect", label: "paypal" },
      createOrder: async () => {
        try {
          const {buyerName, buyerEmail} = customer();
          message("Opening secure payment…");
          const order = await json("/api/checkout/paypal/create-order", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({packageCode,buyerName,buyerEmail})});
          return order.id;
        } catch (error) {
          message(error.message, "error");
          throw error;
        }
      },
      onApprove: async data => {
        try {
          message("Confirming payment and preparing your eSIM…");
          await json("/api/checkout/paypal/capture-order", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({orderId:data.orderID})});
          message("Payment completed. Your eSIM QR will arrive by email shortly.", "success");
        } catch (error) { message(error.message, "error"); }
      },
      onCancel: () => message("Payment was cancelled. You have not been charged."),
      onError: () => message("PayPal could not start. Please try again.", "error")
    }).render("#paypal-buttons");
    message("Enter your details, then choose PayPal or an available card option.");
  };
  script.onerror = () => message("PayPal is temporarily unavailable. Please try again.", "error");
  document.head.appendChild(script);
} catch (error) {
  message(error.message, "error");
}
