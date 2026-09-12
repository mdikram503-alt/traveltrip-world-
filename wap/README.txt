Traveler eSIM — WAP / mobile web
================================

There is NO separate WML (Wireless Markup Language) site.

Why
---
WML / WAP 1.x gateways died years ago. Every modern phone
(including feature phones that still browse) speaks HTML5.

The mobile experience IS the website in the web/ folder.

How to open it on a phone
-------------------------
1. Copy web/ onto the device and open index.html, or
2. Serve web/ on your LAN:

     cd web
     python3 -m http.server 8080

   Then on the phone visit http://<your-pc-ip>:8080

3. Deploy web/ to any static host (Netlify, Cloudflare Pages,
   S3+CloudFront, nginx). The layout is mobile-first.

Design notes
------------
- Viewport + touch targets are sized for one-hand use.
- No hover-only actions.
- Checkout works without a bundler.
- "Add to Home Screen" meta tags are in web/index.html
  so it behaves like a lightweight web-app / WAP bookmark.

If you later need a true offline wrapper, wrap web/ with
Trusted Web Activity (Android) or a WKWebView shell (iOS).
The Android Kotlin app in android/ is the first-class
native client and does not embed this site.
