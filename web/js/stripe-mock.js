/** Demo checkout. Swap for Stripe.js + PaymentIntent when keys exist. */
export async function payMock({ amount, email, planId }) {
  await new Promise(r => setTimeout(r, 700));
  if (!email || !email.includes("@")) throw new Error("Valid email required");
  const id = "ord_" + Math.random().toString(36).slice(2, 10);
  const qr = "LPA:1$smdp.traveleresim.example$" + id.toUpperCase();
  localStorage.setItem("traveler.lastOrder", JSON.stringify({
    id, amount, email, planId, qr, status: "PAID", at: Date.now()
  }));
  return { id, qr, status: "PAID" };
}
