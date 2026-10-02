class AppConfig {
  // Live Production Backend URL
  static const String baseUrl = "https://traveltrip.world";
  // Local Android Emulator fallback: "http://10.0.2.2:8000";
  // Local iOS Simulator / Desktop fallback: "http://127.0.0.1:8000";

  // Stripe Gateway Configuration
  static const String stripePublishableKey = "pk_live_your_publishable_key";
  static const String merchantDisplayName = "TravelTrip.World";

  // PayPal Gateway Configuration
  static const String paypalClientId = "PAYPAL_CLIENT_ID";
  static const String paypalSecret = "PAYPAL_SECRET_KEY";

  // Official Support Contacts
  static const String officialEmail = "hello@traveltrip.world";
  static const String supportEmail = "support@traveltrip.world";
  static const String whatsappSupport = "+971524413931";

  // API Endpoints (100% matched with backend routes)
  static const String endpointCreatePaymentIntent = "/create-payment-intent";
  static const String endpointCreatePaypalOrder = "/create-paypal-order";
  static const String endpointPackages = "/api/packages";
  static const String endpointFlights = "/api/flights";
  static const String endpointHotels = "/api/hotels";
  static const String endpointTours = "/api/tours";
  static const String endpointVisa = "/api/visa";
  static const String endpointWallet = "/api/wallet";
  static const String endpointVip = "/api/vip";
  static const String endpointAiPlanner = "/api/ai/planner";
  static const String endpointLogin = "/api/login";
  static const String endpointRegister = "/api/register";
}
