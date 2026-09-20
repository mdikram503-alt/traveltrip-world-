# Traveler mobile app

This branch is reserved for the shared Python/Kivy Android and iOS mobile application.

The app must use only Traveler branding and consume customer-safe server APIs. It must never contain Stripe, supplier, admin, or signing secrets.

## Required flows

- Browse eSIM plans from the server catalog
- Secure server-created checkout handoff
- Sign in and customer order history
- QR/activation details after backend fulfilment
- Support and installation guidance

## Build targets

- Android APK/AAB: Buildozer with Android SDK and a release keystore held outside source control
- iOS: macOS/Xcode with Apple Developer signing and TestFlight

The existing `public/downloads/TravelTrip_Android.apk` remains unchanged until a tested replacement release is produced. The existing iOS IPA is a placeholder and must not be presented as an iOS app release.
