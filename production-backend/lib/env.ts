const required = (name: string) => { const value = process.env[name]; if (!value) throw new Error(`Missing required environment variable: ${name}`); return value; };
const requiredOneOf = (...names: string[]) => {
  for (const name of names) {
    const value = process.env[name];
    if (value) return value;
  }
  throw new Error(`Missing required environment variable: ${names.join(" or ")}`);
};
export const env = {
  databaseUrl: () => requiredOneOf("NEON_DATABASE_URL", "DATABASE_URL"),
  resellKey: () => required("RESELLPORTAL_API_KEY"),
  resellSecret: () => required("RESELLPORTAL_API_SECRET"),
  paypalClientId: () => required("PAYPAL_CLIENT_ID"),
  paypalClientSecret: () => required("PAYPAL_CLIENT_SECRET"),
  paypalWebhookId: () => required("PAYPAL_WEBHOOK_ID"),
  paypalBase: () => process.env.PAYPAL_MODE === "sandbox" ? "https://api-m.sandbox.paypal.com" : "https://api-m.paypal.com",
  sellingMarginBps: () => { const value = Number(process.env.SELLING_MARGIN_BPS || "2500"); if (!Number.isInteger(value) || value < 0 || value > 100000) throw new Error("SELLING_MARGIN_BPS must be an integer between 0 and 100000"); return value; },
  smtp: () => ({host:required("SMTP_HOST"), port:Number(process.env.SMTP_PORT || "587"), user:required("SMTP_USER"), pass:required("SMTP_APP_PASSWORD"), from:required("EMAIL_FROM")})
};
