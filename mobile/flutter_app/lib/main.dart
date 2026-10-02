import 'package:flutter/material.dart';
import 'constants/theme.dart';
import 'services/stripe_service.dart';
import 'screens/splash_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Stripe Service with Publishable Key
  await StripeService.initialize();

  runApp(
    const TravelTripWorld(),
  );
}

class TravelTripWorld extends StatelessWidget {
  const TravelTripWorld({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TravelTrip.World',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const SplashScreen(),
    );
  }
}
