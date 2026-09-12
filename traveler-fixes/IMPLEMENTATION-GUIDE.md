# 🎯 Traveler eSIM — Complete Implementation Guide

**এই গাইড অনুসরণ করলে আপনার সাইট সম্পূর্ণভাবে production-ready হবে।**

---

## 📋 কী ফিক্স করা হয়েছে

✅ **Password Reset** — সম্পূর্ণ implementation  
✅ **Email Verification** — OTP + verification flow  
✅ **PayPal Integration** — Complete payment gateway  
✅ **Better Auth** — Origin configuration fixed  
✅ **Email Templates** — Professional templates সহ  
✅ **ResellPortal Bridge** — Credential validation  
✅ **Google OAuth** — Origin settings fixed  

---

## 🔧 ইমপ্লিমেন্টেশন স্টেপস

### **ধাপ ১ — Server Routes যোগ করো**

তোমার `server/` ফোল্ডারে এই ফাইলগুলো add করো:

```
server/
├── routes/
│   ├── auth-enhanced.mjs          [ADD THIS]
│   ├── paypal.mjs                 [ADD THIS]
│   └── (existing files)
├── config/
│   ├── auth.mjs                   [REPLACE THIS]
│   └── (existing files)
└── templates/
    ├── email-templates.mjs        [ADD THIS]
    └── (existing files)
```

### **ধাপ ২ — Main App File Update করো**

তোমার `server/app.mjs` বা `server/main.mjs`-এ এই routes import করো:

```javascript
import authEnhanced from './routes/auth-enhanced.mjs';
import paypalRoutes from './routes/paypal.mjs';
import auth from './config/auth.mjs';

// Add routes
app.use('/api', authEnhanced);
app.use('/api', paypalRoutes);
app.use('/api', auth);
```

### **ধাপ ৩ — Environment Variables Set করো (Vercel)**

এই variables যোগ করো (পূর্বে যুক্ত করেছ):

```
✅ PAYPAL_CLIENT_ID
✅ PAYPAL_CLIENT_SECRET
✅ GOOGLE_CLIENT_ID
✅ GOOGLE_CLIENT_SECRET
✅ RESELLPORTAL_API_KEY
✅ RESELLPORTAL_API_SECRET
✅ DATABASE_URL
✅ BETTER_AUTH_SECRET
✅ GMAIL_SERVICE_ACCOUNT (if using Gmail API)
```

**Check করো যে "Needs Attention" marked variables সঠিক values দিয়ে update হয়েছে।**

### **ধাপ ৪ — Frontend Pages যোগ করো**

এই ফাইলগুলো `web/pages/` ফোল্ডারে যোগ করো:

```
web/pages/
├── reset-password.html            [ADD THIS]
├── verify-email.html              [ADD THIS]
├── account.html                   [UPDATE - add forgot password link]
└── (existing files)
```

### **ধাপ ৫ — Account Page Update করো**

`web/pages/account.html`-এ এই লিংক যোগ করো (Forgot Password section-এ):

```html
<a href="./account.html?action=forgot-password">Forgot Password?</a>
```

এবং JavaScript-এ handle করো:

```javascript
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('action') === 'forgot-password') {
  showForgotPasswordForm();
}
```

### **ধাপ ৬ — Database Migrations**

নিচের নতুন columns add করো:

```sql
-- Users table-এ add করো:
ALTER TABLE users ADD COLUMN reset_token VARCHAR(255);
ALTER TABLE users ADD COLUMN reset_token_expires DATETIME;
ALTER TABLE users ADD COLUMN verification_token VARCHAR(255);
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0;

-- Orders table-এ add করো:
ALTER TABLE orders ADD COLUMN payment_method VARCHAR(50);
ALTER TABLE orders ADD COLUMN payment_status VARCHAR(50);

-- নতুন eSIMs table:
CREATE TABLE esims (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_id VARCHAR(255),
  email VARCHAR(255),
  country VARCHAR(100),
  package VARCHAR(100),
  status VARCHAR(50),
  qr_code LONGTEXT,
  activation_code VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
```

### **ধাপ ৭ — Email Configuration**

আপনার email service সেটআপ করো (Gmail, SendGrid, etc.):

**Gmail Service Account ব্যবহার করলে:**
```javascript
// server/integrations/email.mjs
import nodemailer from 'nodemailer';

const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: process.env.GMAIL_USER,
    pass: process.env.GMAIL_APP_PASSWORD,
  }
});

export async function sendEmail({ to, subject, html }) {
  return transporter.sendMail({
    from: 'noreply@traveltrip.world',
    to,
    subject,
    html,
  });
}
```

---

## 🧪 Testing (গুরুত্বপূর্ণ!)

### **Test Cases:**

1. **Password Reset:**
   - [ ] User clicks "Forgot Password"
   - [ ] Email পায় reset link দিয়ে
   - [ ] Link click করে new password set করে
   - [ ] নতুন password দিয়ে login করতে পারে

2. **Email Verification:**
   - [ ] User signup করে
   - [ ] Verification email পায়
   - [ ] Link click করে email verify করে
   - [ ] Profile page সঠিকভাবে খোলে

3. **PayPal Payment:**
   - [ ] Checkout page-এ PayPal button visible
   - [ ] Click করে PayPal লগইন করে
   - [ ] Payment সফলভাবে করে
   - [ ] Order confirmation email পায় QR code দিয়ে

4. **Google Login:**
   - [ ] "Login with Google" button visible
   - [ ] Click করে Google-এ সাইন ইন করে
   - [ ] Account successfully created

5. **ResellPortal Integration:**
   - [ ] eSIM প্রোভিশনিং কাজ করছে
   - [ ] No 401 errors আসছে
   - [ ] QR code সঠিকভাবে জেনারেট হচ্ছে

---

## 🚀 Deployment

### **GitHub-এ Push করো:**

```bash
git add .
git commit -m "feat: add password reset, email verification, PayPal integration, and auth fixes"
git push origin main
```

### **Vercel Deploy করবে automatically**

আপনার Vercel dashboard-এ গিয়ে check করো:
- [ ] Build successful?
- [ ] No errors?
- [ ] All environment variables set?

---

## ⚙️ Production Checklist

Before going live, verify:

- [ ] SSL/HTTPS enabled
- [ ] All email tests pass
- [ ] PayPal live mode credentials set (sandbox পরে)
- [ ] ResellPortal API working
- [ ] Database backups configured
- [ ] Error logging enabled (Sentry, etc.)
- [ ] CORS properly configured
- [ ] Rate limiting on auth endpoints
- [ ] GDPR compliance checked
- [ ] Privacy Policy updated
- [ ] Terms of Service reviewed

---

## 📞 Support URLs (update করো)

```
Support Email: support@traveltrip.world
Help Center: https://traveltrip.world/pages/help.html
Contact Form: https://traveltrip.world/pages/contact.html
Status Page: https://status.traveltrip.world
```

---

## 🆘 Troubleshooting

### **যদি PayPal কাজ না করে:**
- Check করো PAYPAL_CLIENT_ID এবং SECRET সঠিক আছে কিনা
- Verify করো redirect URLs সেট করেছ PayPal dashboard-এ
- Check করো webhook কনফিগার করেছ কিনা

### **যদি Email না পাঠায়:**
- Gmail: App password generate করেছ কিনা
- SendGrid: API key valid আছে কিনা
- Check করো email templates সঠিক HTML দিচ্ছে কিনা

### **যদি ResellPortal 401 দেয়:**
- Verify করো API key/secret সঠিক
- Check করো credentials expired হয়নি
- Test mode enable করেছ কিনা

### **যদি Google Login কাজ না করে:**
- Verify করো Google Cloud-এ redirect URLs সেট করেছ:
  - `https://traveltrip.world/api/auth/callback/google`
  - `https://traveler-esim.vercel.app/api/auth/callback/google`
- Check করো CLIENT_ID এবং SECRET correct আছে

---

## 📊 Monitoring

এই metrics track করো:

- Sign-up success rate
- Email verification rate
- Password reset usage
- Payment success rate
- eSIM provisioning time
- Error rates

---

## 🎯 Next Steps (Post-Launch)

1. **Phone OTP**: SMS verification implement করো (Twilio)
2. **Analytics**: Google Analytics + Mixpanel add করো
3. **Performance**: Caching layer add করো (Redis)
4. **Mobile App**: iOS/Android native app development
5. **Localization**: Multiple languages support

---

**সব কিছু implement করলে তোমার Traveler eSIM store সম্পূর্ণভাবে production-ready হবে এবং professional লাগবে।**

**কোনো প্রশ্ন থাকলে এই গাইড ফিরে পড়ো অথবা support-এ যোগাযোগ করো।**

---

**Last Updated:** September 12, 2026  
**Version:** 1.0.0 - Complete Implementation
