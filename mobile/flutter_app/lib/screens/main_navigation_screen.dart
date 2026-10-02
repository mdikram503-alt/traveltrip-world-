import 'package:flutter/material.dart';
import '../constants/theme.dart';
import 'home_screen.dart';
import 'flights_screen.dart';
import 'esim_marketplace_screen.dart';
import 'hotels_screen.dart';
import 'visa_screen.dart';
import 'wallet_screen.dart';
import 'vip_screen.dart';
import 'ai_planner_screen.dart';

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    HomeScreen(),
    FlightsScreen(),
    EsimMarketplaceScreen(),
    HotelsScreen(),
    _MoreMenuScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        type: BottomNavigationBarType.fixed,
        backgroundColor: AppColors.primary,
        selectedItemColor: AppColors.gold,
        unselectedItemColor: AppColors.textMuted,
        selectedFontSize: 11,
        unselectedFontSize: 11,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_rounded),
            label: "Home",
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.flight_takeoff_rounded),
            label: "Flights",
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.sim_card_rounded),
            label: "eSIM 5G",
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.hotel_rounded),
            label: "Hotels",
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.grid_view_rounded),
            label: "Services",
          ),
        ],
      ),
    );
  }
}

class _MoreMenuScreen extends StatelessWidget {
  const _MoreMenuScreen();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text("Super App Services"),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _menuItem(
            context,
            title: "🛂 Visa Services",
            subtitle: "UAE, Saudi, Schengen, Singapore, Thailand eVisa",
            icon: Icons.badge_rounded,
            color: const Color(0xFFA855F7),
            screen: const VisaScreen(),
          ),
          _menuItem(
            context,
            title: "💳 Travel Wallet & Cashback",
            subtitle: "\$25.50 Balance • 5% eSIM Cashback • Points",
            icon: Icons.account_balance_wallet_rounded,
            color: const Color(0xFF10B981),
            screen: const WalletScreen(),
          ),
          _menuItem(
            context,
            title: "👑 VIP Club Membership",
            subtitle: "Gold & Platinum Tiers • Airport Lounge • Concierge",
            icon: Icons.workspace_premium_rounded,
            color: AppColors.gold,
            screen: const VipScreen(),
          ),
          _menuItem(
            context,
            title: "🤖 AI Trip Planner",
            subtitle: "Personalized itineraries & smart budget calculator",
            icon: Icons.auto_awesome_rounded,
            color: AppColors.accentCyan,
            screen: const AiPlannerScreen(),
          ),
          _menuItem(
            context,
            title: "👤 Traveler Profile & Orders",
            subtitle: "Guest Traveler • support@traveltrip.world",
            icon: Icons.person_rounded,
            color: AppColors.white,
            screen: const WalletScreen(),
          ),
        ],
      ),
    );
  }

  Widget _menuItem(
    BuildContext context, {
    required String title,
    required String subtitle,
    required IconData icon,
    required Color color,
    required Widget screen,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: AppColors.primary,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: color.withOpacity(0.3)),
          ),
          child: Icon(icon, color: color, size: 22),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
        subtitle: Text(subtitle, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
        trailing: const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: AppColors.textMuted),
        onTap: () {
          Navigator.of(context).push(MaterialPageRoute(builder: (_) => screen));
        },
      ),
    );
  }
}
