Traveler eSIM — Full Source Package
===================================
Package: traveler-esim-full-source
Version: 1.0.0-source
Application ID (Android): com.traveleresim.app
Brand: Traveler eSIM

WHAT IS IN THIS ZIP
-------------------
  web/                 Website. Also the mobile / "WAP" experience.
                       Open web/index.html in any browser (phone or desktop).
  android/             Real Kotlin Android app (package com.traveleresim.app).
                       Open the android/ folder in Android Studio.
  wap/README.txt       Explains why there is no separate WML site.
  TRAVELER-README.txt  This file.

NOT INCLUDED (on purpose)
-------------------------
  - node_modules
  - compiled APK / AAB
  - iOS / Xcode project  (not built yet)
  - live Stripe secret keys
  - live carrier / eSIM provisioning API keys
  - Google Maps / Firebase production keys

HOW TO RUN THE WEBSITE
----------------------
Option A — no install:
  Open web/index.html in Chrome, Safari, or Firefox.
  On a phone, copy the web/ folder to the device or serve it over LAN.

Option B — local server (recommended so checkout / fetch work):
  cd web
  python3 -m http.server 8080
  Then open http://127.0.0.1:8080

Option C — if you add a bundler later:
  cd web
  npm install          # only if you introduce a package.json workflow
  npm run dev

The site is static HTML + CSS + vanilla JS.
Plans and countries load from web/data/*.json.
Checkout talks to a mock payment layer (see web/js/stripe-mock.js).
Replace STRIPE_PUBLISHABLE_KEY and API_BASE in web/js/config.js
before going live.

HOW TO RUN THE ANDROID APP
--------------------------
1. Install Android Studio Ladybug / Koala or newer (AGP 8.7 compatible).
2. File → Open → select the android/ directory (NOT the zip root).
3. Let Gradle sync. First sync downloads the Gradle wrapper jars
   if they are missing from gradle/wrapper/.
4. Create a virtual device (Pixel 7, API 34) or plug in a phone
   with USB debugging.
5. Run the "app" configuration.

Local flavor uses mock catalog + mock wallet.
To point at a real backend, edit:
  android/app/src/main/java/com/traveleresim/app/core/ApiConfig.kt

eSIM INSTALL ON DEVICE
----------------------
Real one-tap eSIM download requires:
  - carrier / SM-DP+ credentials
  - EuiccManager + LPA (Local Profile Assistant)
  - an activation code (LPA:1$smdp.example$matching-id)

This source ships a DemoEuiccManager that shows the install
flow and falls back to "scan QR / open system eSIM settings".
Do not ship the demo manager to production.

STRIPE / PAYMENTS
-----------------
web/js/stripe-mock.js and the Android CheckoutViewModel
accept a card in test mode and mark the order PAID locally.

When you have keys:
  Web:     set window.TRAVELER_CONFIG.stripePk in web/js/config.js
  Android: set BuildConfig.STRIPE_PK via local.properties
           (see android/local.properties.example)

Never commit sk_live_ or sk_test_ secret keys.

PROJECT MAP
-----------
web/
  index.html                 Home / destinations
  pages/                     plans, checkout, account, help, coverage, legal
  css/                       tokens, layout, components
  js/                        catalog, cart, auth-mock, stripe-mock, i18n
  data/countries.json        190+ destinations (sample subset + regions)
  data/plans.json            Local / regional / global plans

android/
  settings.gradle.kts
  build.gradle.kts
  gradle.properties
  app/build.gradle.kts
  app/src/main/AndroidManifest.xml
  app/src/main/java/com/traveleresim/app/
      TravelerApp.kt
      MainActivity.kt
      core/                  API, config, result types
      data/                  repository, models, mock
      domain/                use-cases
      ui/                    Compose screens + theme
      esim/                  DemoEuicc + QR
  app/src/main/res/          themes, strings (en + bn), drawables

iOS
---
Not in this package. Next milestone if you want it:
  SwiftUI app, same package-style bundle id com.traveleresim.app,
  StoreKit 2 + Stripe iOS, eSIM via CTCellularPlanProvisioning
  (entitlement required from Apple).

LICENSE / USE
-------------
Source is provided as a working starter for Traveler eSIM.
Replace branding, legal pages, and keys before public release.
Dummy prices are not a commercial offer.

Support contact placeholder: support@traveleresim.example
