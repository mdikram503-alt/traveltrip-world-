import 'package:flutter/material.dart';
import '../constants/theme.dart';
import '../services/api_service.dart';
import 'checkout_screen.dart';

class WalletScreen extends StatefulWidget {
  const WalletScreen({super.key});

  @override
  State<WalletScreen> createState() => _WalletScreenState();
}

class _WalletScreenState extends State<WalletScreen> {
  Map<String, dynamic>? _wallet;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadWallet();
  }

  Future<void> _loadWallet() async {
    final w = await ApiService.fetchWallet();
    if (mounted) {
      setState(() {
        _wallet = w;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final balance = (_wallet?['balanceUsd'] as num?)?.toDouble() ?? 25.50;
    final cashback = (_wallet?['cashbackEarnedUsd'] as num?)?.toDouble() ?? 12.0;
    final points = _wallet?['rewardPoints'] ?? 450;
    final referralCode = _wallet?['referralCode'] ?? "TRIP786";

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text("Travel Wallet & Rewards"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.gold))
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Main Balance Card
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFF0B132B), Color(0xFF1C2541)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppColors.gold, width: 1.5),
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.gold.withOpacity(0.15),
                          blurRadius: 20,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: const [
                            Text("Available Wallet Balance", style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                            Icon(Icons.contactless_rounded, color: AppColors.gold, size: 28),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Text(
                          "\$${balance.toStringAsFixed(2)} USD",
                          style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w900, color: AppColors.gold),
                        ),
                        const SizedBox(height: 20),
                        Row(
                          children: [
                            Expanded(
                              child: ElevatedButton.icon(
                                onPressed: () {
                                  Navigator.of(context).push(
                                    MaterialPageRoute(
                                      builder: (_) => const CheckoutScreen(
                                        title: "Top-up TravelTrip Wallet Balance",
                                        amount: 50.0,
                                        serviceType: "wallet",
                                      ),
                                    ),
                                  );
                                },
                                icon: const Icon(Icons.add_circle_outline_rounded, color: AppColors.primary, size: 18),
                                label: const Text("Top Up (+\$50)"),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppColors.gold,
                                  foregroundColor: AppColors.primary,
                                  padding: const EdgeInsets.symmetric(vertical: 12),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Rewards & Cashback Grid
                  Row(
                    children: [
                      Expanded(
                        child: Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text("Cashback Earned", style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                                const SizedBox(height: 6),
                                Text("\$${cashback.toStringAsFixed(2)}", style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.success)),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text("Reward Points", style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                                const SizedBox(height: 6),
                                Text("$points pts", style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: AppColors.accentCyan)),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 20),

                  // Cashback Rates
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: const [
                          Text("Cashback Guarantee", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                          SizedBox(height: 12),
                          ListTile(
                            contentPadding: EdgeInsets.zero,
                            leading: Icon(Icons.sim_card_rounded, color: AppColors.gold),
                            title: Text("5% Cashback on all eSIM Orders"),
                            dense: true,
                          ),
                          ListTile(
                            contentPadding: EdgeInsets.zero,
                            leading: Icon(Icons.flight_takeoff_rounded, color: AppColors.accentCyan),
                            title: Text("2% Cashback on Flight Bookings"),
                            dense: true,
                          ),
                          ListTile(
                            contentPadding: EdgeInsets.zero,
                            leading: Icon(Icons.hotel_rounded, color: Color(0xFFF59E0B)),
                            title: Text("3% Cashback on Hotel Reservations"),
                            dense: true,
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Referral Program
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text("Refer a Friend & Earn \$10", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.gold)),
                          const SizedBox(height: 6),
                          const Text(
                            "Share your invite code with fellow travelers. When they buy an eSIM or book a flight, you both get \$10 credit!",
                            style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
                          ),
                          const SizedBox(height: 14),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                            decoration: BoxDecoration(
                              color: AppColors.primary,
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(color: AppColors.cardBorder),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(referralCode, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, letterSpacing: 2, color: AppColors.white)),
                                IconButton(
                                  icon: const Icon(Icons.copy_rounded, color: AppColors.gold),
                                  onPressed: () {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(content: Text("Referral code copied to clipboard!")),
                                    );
                                  },
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
