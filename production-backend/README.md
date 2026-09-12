# Traveltrip production backend

This Next.js service creates PayPal orders from supplier prices on the server, verifies signed PayPal capture webhooks, and then provisions eSIMs through ResellPortal. It never accepts an amount from the browser.

## Deploy

1. Create a managed PostgreSQL database and run `db/schema.sql` once.
2. Connect Neon with prefix `NEON` so Vercel creates `NEON_URL`, then add the remaining values from `.env.example` in Vercel's Production environment. Do not commit `.env.local` or secrets.
3. Deploy this directory as the Vercel project root.
4. In the PayPal live app, register `https://traveltrip.world/api/paypal/webhook` and select `PAYMENT.CAPTURE.COMPLETED`. Copy its webhook ID into `PAYPAL_WEBHOOK_ID`.
5. Use the returned PayPal order ID with the PayPal JavaScript SDK's capture flow.

## Operational safeguards

- `SELLING_MARGIN_BPS` is the server-controlled margin (2500 means 25%).
- A webhook must pass PayPal signature verification, match a stored PayPal order, and match the stored USD amount before fulfillment.
- Webhook event IDs are deduplicated. An order enters `FULFILLING` before contacting ResellPortal, avoiding duplicate eSIM supply. A failed supplier or email delivery is recorded for reconciliation; never retry an eSIM order blindly.
- Add an authenticated operations dashboard or scheduled reconciliation worker before broad public launch so `FULFILLMENT_FAILED` and `FULFILLED_EMAIL_PENDING` orders are handled promptly.
