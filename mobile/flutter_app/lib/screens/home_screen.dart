import 'package:flutter/material.dart';
import '../constants/theme.dart';
import '../models/esim_package.dart';
import '../models/flight.dart';
import '../services/api_service.dart';
import 'checkout_screen.dart';
import 'esim_marketplace_screen.dart';
import 'flights_screen.dart';
import 'hotels_screen.dart';
import 'visa_screen.dart';
import 'wallet_screen.dart';
import 'vip_screen.dart';
import 'ai_planner_screen.dart';

class HomeScreen extends StatefulWidget {
  final Function(int)? onNavigateTab;

  const HomeScreen({super.key, this.onNavigateTab});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<EsimPackage> _featuredPackages = [];
  List<Flight> _featuredFlights = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadHomeData();
  }

  Future<void> _loadHomeData() async {
    final pkgs = await ApiService.fetchPackages(locationCode: "BD");
    final flights = await ApiService.fetchFlights();
    if (mounted) {
      setState(() {
        _featuredPackages = pkgs.take(4).toList();
        _featuredFlights = flights.take(3).toList();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: const [
            Icon(Icons.public_rounded, color: AppColors.gold, size: 24),
            SizedBox(width: 8),
            Text("TravelTrip.World"),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_none_rounded),
            onPressed: () {},
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadHomeData,
        color: AppColors.gold,
        backgroundColor: AppColors.card,
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // VIP & Wallet Bar
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFF141D38), Color(0xFF1C2541)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.cardBorder),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text("Welcome Traveler", style: TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                        const SizedBox(height: 2),
                        Row(
                          children: const [
                            Text("VIP Gold Member", style: TextStyle(color: AppColors.gold, fontWeight: FontWeight.bold, fontSize: 15)),
                            SizedBox(width: 6),
                            Icon(Icons.verified_rounded, color: AppColors.gold, size: 16),
                          ],
                        ),
                      ],
                    ),
                    GestureDetector(
                      onTap: () {
                        Navigator.of(context).push(MaterialPageRoute(builder: (_) => const WalletScreen()));
                      },
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: AppColors.primary,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(color: AppColors.gold.withOpacity(0.5)),
                        ),
                        child: Row(
                          children: const [
                            Icon(Icons.account_balance_wallet_rounded, color: AppColors.gold, size: 16),
                            SizedBox(width: 6),
                            Text("\$25.50 USD", style: TextStyle(color: AppColors.white, fontWeight: FontWeight.bold, fontSize: 13)),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // Super App 8-Service Grid
              const Text("Explore Services", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              GridView.count(
                crossAxisCount: 4,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: 0.85,
                children: [
                  _buildServiceIcon("Flights", Icons.flight_takeoff_rounded, AppColors.accentCyan, () {
                    Navigator.of(context).push(MaterialPageRoute(builder: (_) => const FlightsScreen()));
                  }),
                  _buildServiceIcon("Hotels", Icons.hotel_rounded, const Color(0xFFF59E0B), () {
                    Navigator.of(context).push(MaterialPageRoute(builder: (_) => const HotelsScreen()));
                  }),
                  _buildServiceIcon("eSIM 5G", Icons.sim_card_rounded, AppColors.success, () {
                    Navigator.of(context).push(MaterialPageRoute(builder: (_) => const EsimMarketplaceScreen()));
                  }),
                  _buildServiceIcon("Visa", Icons.badge_rounded, const Color(0xFFA855F7), () {
                    Navigator.of(context).push(MaterialPageRoute(builder: (_) => const VisaScreen()));
                  }),
                  _buildServiceIcon("AI Planner", Icons.auto_awesome_rounded, AppColors.gold, () {
                    Navigator.of(context).push(MaterialPageRoute(builder: (_) => const AiPlannerScreen()));
                  }),
                  _buildServiceIcon("Wallet", Icons.account_balance_wallet_rounded, const Color(0xFF10B981), () {
                    Navigator.of(context).push(MaterialPageRoute(builder: (_) => const WalletScreen()));
                  }),
                  _buildServiceIcon("VIP Club", Icons.workspace_premium_rounded, AppColors.gold, () {
                    Navigator.of(context).push(MaterialPageRoute(builder: (_) => const VipScreen()));
                  }),
                  _buildServiceIcon("Tours", Icons.explore_rounded, const Color(0xFFEC4899), () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text("Bespoke Tour Packages available in Explore tab.")),
                    );
                  }),
                ],
              ),

              const SizedBox(height: 24),

              // ResellPortal Wholesale Sync Badge
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: AppColors.success.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppColors.success.withOpacity(0.4)),
                ),
                child: Row(
                  children: const [
                    Icon(Icons.cloud_sync_rounded, color: AppColors.success, size: 20),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        "ResellPortal Wholesale Live Sync • 117+ Packages Active",
                        style: TextStyle(color: AppColors.success, fontSize: 12, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // Featured eSIMs Section
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text("Popular Travel eSIMs", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  TextButton(
                    onPressed: () {
                      Navigator.of(context).push(MaterialPageRoute(builder: (_) => const EsimMarketplaceScreen()));
                    },
                    child: const Text("View All", style: TextStyle(color: AppColors.gold)),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              if (_isLoading)
                const Center(child: Padding(padding: EdgeInsets.all(20.0), child: CircularProgressIndicator(color: AppColors.gold)))
              else
                ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: _featuredPackages.length,
                  itemBuilder: (ctx, i) {
                    final pkg = _featuredPackages[i];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: AppColors.primary,
                          child: const Icon(Icons.wifi_tethering_rounded, color: AppColors.gold, size: 22),
                        ),
                        title: Text(pkg.name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                        subtitle: Text("${pkg.data} • ${pkg.validity} • 5G Speed", style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                        trailing: ElevatedButton(
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
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.gold,
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                          ),
                          child: Text("\$${pkg.priceUsd.toStringAsFixed(2)}", style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                        ),
                      ),
                    );
                  },
                ),

              const SizedBox(height: 20),

              // Flight Radar Spotlight
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text("Live Premier Airlines", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  TextButton(
                    onPressed: () {
                      Navigator.of(context).push(MaterialPageRoute(builder: (_) => const FlightsScreen()));
                    },
                    child: const Text("Search", style: TextStyle(color: AppColors.gold)),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              if (_featuredFlights.isNotEmpty)
                ..._featuredFlights.map((f) => Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(f.airline, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.gold)),
                            Text("\$${f.priceUsd.toStringAsFixed(0)} USD", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text("${f.originCode} (${f.originCity})", style: const TextStyle(color: AppColors.white, fontSize: 14)),
                            const Icon(Icons.arrow_forward_rounded, color: AppColors.textSecondary, size: 16),
                            Text("${f.destinationCode} (${f.destinationCity})", style: const TextStyle(color: AppColors.white, fontSize: 14)),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text("${f.aircraft} • ${f.duration} • ${f.badge}", style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                      ],
                    ),
                  ),
                )),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildServiceIcon(String label, IconData icon, Color color, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            width: 54,
            height: 54,
            decoration: BoxDecoration(
              color: AppColors.card,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: color.withOpacity(0.35)),
            ),
            child: Icon(icon, color: color, size: 26),
          ),
          const SizedBox(height: 6),
          Text(
            label,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.white),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}
