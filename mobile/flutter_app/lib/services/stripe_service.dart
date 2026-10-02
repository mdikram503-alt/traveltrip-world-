import 'package:flutter/material.dart';
import 'package:flutter_stripe/flutter_stripe.dart';
import '../constants/config.dart';

class StripeService {
  /// Initializes Stripe with publishable key and sets merchant configuration.
  static Future<void> initialize({String? publishableKey}) async {
    Stripe.publishableKey = publishableKey ?? AppConfig.stripePublishableKey;
    await Stripe.instance.applySettings();
  }

  /// Presents the native Stripe Payment Sheet for Apple Pay, Google Pay, and Cards.
  static Future<bool> makePayment({
    required String clientSecret,
    String? merchantDisplayName,
  }) async {
    try {
      await Stripe.instance.initPaymentSheet(
        paymentSheetParameters: SetupPaymentSheetParameters(
          paymentIntentClientSecret: clientSecret,
          merchantDisplayName: merchantDisplayName ?? AppConfig.merchantDisplayName,
          style: ThemeMode.dark,
          appearance: const PaymentSheetAppearance(
            colors: PaymentSheetAppearanceColors(
              primary: Color(0xFFD4AF37),
              background: Color(0xFF0B132B),
              componentBackground: Color(0xFF141D38),
              componentBorder: Color(0xFF26335C),
              componentText: Colors.white,
              primaryText: Colors.white,
              secondaryText: Color(0xFF94A3B8),
            ),
          ),
        ),
      );

      await Stripe.instance.presentPaymentSheet();
      return true;
    } on StripeException catch (e) {
      if (e.error.code == FailureCode.Canceled) {
        debugPrint("[STRIPE] Payment sheet cancelled by user.");
      } else {
        debugPrint("[STRIPE ERROR] ${e.error.localizedMessage}");
      }
      return false;
    } catch (e) {
      debugPrint("[STRIPE EXCEPTION] $e");
      return false;
    }
  }
}
