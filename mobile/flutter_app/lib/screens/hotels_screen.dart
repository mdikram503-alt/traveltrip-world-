import 'package:flutter/material.dart';
import '../constants/theme.dart';
import '../models/hotel.dart';
import '../services/api_service.dart';
import 'checkout_screen.dart';

class HotelsScreen extends StatefulWidget {
  const HotelsScreen({super.key});

  @override
  State<HotelsScreen> createState() => _HotelsScreenState();
}

class _HotelsScreenState extends State<HotelsScreen> {
  List<Hotel> _hotels = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadHotels();
  }

  Future<void> _loadHotels() async {
    final list = await ApiService.fetchHotels();
    if (mounted) {
      setState(() {
        _hotels = list;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text("Curated Luxury Hotels"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.gold))
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _hotels.length,
              itemBuilder: (ctx, i) {
                final h = _hotels[i];
                return Card(
                  margin: const EdgeInsets.only(bottom: 16),
                  clipBehavior: Clip.antiAlias,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        height: 140,
                        color: AppColors.primary,
                        child: Center(
                          child: Icon(Icons.hotel_rounded, size: 64, color: AppColors.gold.withOpacity(0.5)),
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(
                                  child: Text(
                                    h.name,
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17, color: AppColors.white),
                                  ),
                                ),
                                Row(
                                  children: [
                                    const Icon(Icons.star_rounded, color: AppColors.gold, size: 18),
                                    const SizedBox(width: 4),
                                    Text(h.rating.toString(), style: const TextStyle(fontWeight: FontWeight.bold)),
                                  ],
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Text("${h.city}, ${h.country} • ${h.stars}", style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                            const SizedBox(height: 10),
                            Wrap(
                              spacing: 6,
                              runSpacing: 6,
                              children: h.amenities.map((a) => Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                decoration: BoxDecoration(
                                  color: AppColors.primary,
                                  borderRadius: BorderRadius.circular(6),
                                  border: Border.all(color: AppColors.cardBorder),
                                ),
                                child: Text(a, style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                              )).toList(),
                            ),
                            const Divider(height: 24, color: AppColors.cardBorder),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text("From", style: TextStyle(color: AppColors.textMuted, fontSize: 11)),
                                    Text("\$${h.pricePerNightUsd.toStringAsFixed(0)} / night", style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: AppColors.gold)),
                                  ],
                                ),
                                ElevatedButton(
                                  onPressed: () {
                                    Navigator.of(context).push(
                                      MaterialPageRoute(
                                        builder: (_) => CheckoutScreen(
                                          title: "${h.name} (${h.city}) - 1 Night Stay",
                                          amount: h.pricePerNightUsd,
                                          serviceType: "hotel",
                                        ),
                                      ),
                                    );
                                  },
                                  child: const Text("Book Room"),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
    );
  }
}
