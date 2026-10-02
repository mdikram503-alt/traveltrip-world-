import 'package:flutter/material.dart';
import '../constants/theme.dart';
import '../services/api_service.dart';
import 'checkout_screen.dart';

class VipScreen extends StatefulWidget {
  const VipScreen({super.key});

  @override
  State<VipScreen> createState() => _VipScreenState();
}

class _VipScreenState extends State<VipScreen> {
  List<Map<String, dynamic>> _tiers = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadTiers();
  }

  Future<void> _loadTiers() async {
    final t = await ApiService.fetchVipTiers();
    if (mounted) {
      setState(() {
        _tiers = t;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text("VIP Club Membership"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.gold))
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _tiers.length,
              itemBuilder: (ctx, i) {
                final tier = _tiers[i];
                final name = tier['tier'] ?? 'VIP Tier';
                final fee = (tier['feeUsd'] as num?)?.toDouble() ?? 49.0;
                final perks = List<String>.from(tier['perks'] ?? []);
                final isPlatinum = name.contains("Platinum");

                return Card(
                  margin: const EdgeInsets.only(bottom: 20),
                  child: Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: isPlatinum ? const Color(0xFFE5E4E2) : AppColors.gold,
                        width: 1.5,
                      ),
                    ),
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                Icon(
                                  Icons.workspace_premium_rounded,
                                  color: isPlatinum ? const Color(0xFFE5E4E2) : AppColors.gold,
                                  size: 28,
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  name,
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 20,
                                    color: isPlatinum ? const Color(0xFFE5E4E2) : AppColors.gold,
                                  ),
                                ),
                              ],
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: AppColors.primary,
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Text(
                                "\$${fee.toStringAsFixed(0)} / yr",
                                style: const TextStyle(fontWeight: FontWeight.w900, color: AppColors.white),
                              ),
                            ),
                          ],
                        ),
                        const Divider(height: 28, color: AppColors.cardBorder),
                        ...perks.map((p) => Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(Icons.star_rounded, color: AppColors.gold, size: 18),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(p, style: const TextStyle(color: AppColors.white, fontSize: 13)),
                              ),
                            ],
                          ),
                        )),
                        const SizedBox(height: 14),
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: () {
                              Navigator.of(context).push(
                                MaterialPageRoute(
                                  builder: (_) => CheckoutScreen(
                                    title: "$name 1-Year Subscription",
                                    amount: fee,
                                    serviceType: "vip",
                                  ),
                                ),
                              );
                            },
                            style: ElevatedButton.styleFrom(
                              backgroundColor: isPlatinum ? const Color(0xFFE5E4E2) : AppColors.gold,
                              foregroundColor: AppColors.primary,
                            ),
                            child: Text(
                              "Join $name",
                              style: const TextStyle(fontWeight: FontWeight.bold),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }
}
