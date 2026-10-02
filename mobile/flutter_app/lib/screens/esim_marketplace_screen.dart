import 'package:flutter/material.dart';
import '../constants/theme.dart';
import '../models/esim_package.dart';
import '../services/api_service.dart';
import 'checkout_screen.dart';

class EsimMarketplaceScreen extends StatefulWidget {
  const EsimMarketplaceScreen({super.key});

  @override
  State<EsimMarketplaceScreen> createState() => _EsimMarketplaceScreenState();
}

class _EsimMarketplaceScreenState extends State<EsimMarketplaceScreen> {
  final List<Map<String, String>> _destinations = [
    {"code": "BD", "name": "Bangladesh"},
    {"code": "UAE", "name": "UAE (Dubai)"},
    {"code": "IN", "name": "India"},
    {"code": "QA", "name": "Qatar"},
    {"code": "OM", "name": "Oman"},
    {"code": "PK", "name": "Pakistan"},
    {"code": "EU", "name": "Europe (35+)"},
    {"code": "GLOBAL", "name": "Global (140+)"},
    {"code": "TH", "name": "Thailand"},
    {"code": "US", "name": "USA"},
  ];

  String _selectedCc = "BD";
  List<EsimPackage> _packages = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchPackages();
  }

  Future<void> _fetchPackages() async {
    setState(() => _isLoading = true);
    final pkgs = await ApiService.fetchPackages(locationCode: _selectedCc);
    if (mounted) {
      setState(() {
        _packages = pkgs;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text("eSIM Marketplace"),
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Destination Filter Carousel
          Container(
            height: 52,
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              scrollDirection: Axis.horizontal,
              itemCount: _destinations.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (ctx, i) {
                final d = _destinations[i];
                final isSelected = d["code"] == _selectedCc;
                return ChoiceChip(
                  label: Text(d["name"]!),
                  selected: isSelected,
                  selectedColor: AppColors.gold,
                  backgroundColor: AppColors.card,
                  labelStyle: TextStyle(
                    color: isSelected ? AppColors.primary : AppColors.white,
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                    fontSize: 13,
                  ),
                  onSelected: (selected) {
                    if (selected && _selectedCc != d["code"]) {
                      setState(() => _selectedCc = d["code"]!);
                      _fetchPackages();
                    }
                  },
                );
              },
            ),
          ),

          // Subheader Info
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  "Available Plans (${_packages.length})",
                  style: const TextStyle(color: AppColors.textSecondary, fontSize: 13, fontWeight: FontWeight.bold),
                ),
                Row(
                  children: const [
                    Icon(Icons.bolt_rounded, color: AppColors.success, size: 16),
                    SizedBox(width: 4),
                    Text("Instant QR Delivery", style: TextStyle(color: AppColors.success, fontSize: 12)),
                  ],
                ),
              ],
            ),
          ),

          // Packages List
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: AppColors.gold))
                : _packages.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.signal_cellular_off_rounded, size: 48, color: AppColors.textMuted),
                            const SizedBox(height: 12),
                            Text("No packages available for $_selectedCc", style: const TextStyle(color: AppColors.textSecondary)),
                          ],
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        itemCount: _packages.length,
                        itemBuilder: (ctx, i) {
                          final pkg = _packages[i];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Expanded(
                                        child: Text(
                                          pkg.name,
                                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.white),
                                        ),
                                      ),
                                      Text(
                                        "\$${pkg.priceUsd.toStringAsFixed(2)}",
                                        style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 18, color: AppColors.gold),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Row(
                                    children: [
                                      _badge(pkg.data, Icons.data_usage_rounded),
                                      const SizedBox(width: 8),
                                      _badge(pkg.validity, Icons.access_time_rounded),
                                      const SizedBox(width: 8),
                                      _badge("5G / LTE", Icons.speed_rounded),
                                    ],
                                  ),
                                  const SizedBox(height: 10),
                                  Text(
                                    "Network: ${pkg.network}",
                                    style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
                                  ),
                                  const SizedBox(height: 14),
                                  SizedBox(
                                    width: double.infinity,
                                    child: ElevatedButton(
                                      onPressed: () {
                                        Navigator.of(context).push(
                                          MaterialPageRoute(
                                            builder: (_) => CheckoutScreen(
                                              title: pkg.name,
                                              packageCode: pkg.packageCode,
                                              amount: pkg.priceUsd,
                                              serviceType: "esim",
                                            ),
                                          ),
                                        );
                                      },
                                      child: const Text("Buy Now • Instant Activation"),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }

  Widget _badge(String text, IconData icon) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppColors.primary,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: AppColors.cardBorder),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: AppColors.gold),
          const SizedBox(width: 4),
          Text(text, style: const TextStyle(fontSize: 12, color: AppColors.white, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}
