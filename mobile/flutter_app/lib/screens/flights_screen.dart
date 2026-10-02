import 'package:flutter/material.dart';
import '../constants/theme.dart';
import '../models/flight.dart';
import '../services/api_service.dart';
import 'checkout_screen.dart';

class FlightsScreen extends StatefulWidget {
  const FlightsScreen({super.key});

  @override
  State<FlightsScreen> createState() => _FlightsScreenState();
}

class _FlightsScreenState extends State<FlightsScreen> {
  List<Flight> _flights = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadFlights();
  }

  Future<void> _loadFlights() async {
    final list = await ApiService.fetchFlights();
    if (mounted) {
      setState(() {
        _flights = list;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text("Premier Flights"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.gold))
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _flights.length,
              itemBuilder: (ctx, i) {
                final f = _flights[i];
                return Card(
                  margin: const EdgeInsets.only(bottom: 16),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(f.airline, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17, color: AppColors.gold)),
                            Text("\$${f.priceUsd.toStringAsFixed(0)} USD", style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 18)),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text("${f.flightNumber} • ${f.aircraft}", style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                        const Divider(height: 24, color: AppColors.cardBorder),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(f.departureTime, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                                Text(f.originCode, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                                Text(f.originCity, style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
                              ],
                            ),
                            Column(
                              children: [
                                Text(f.duration, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                                const SizedBox(height: 4),
                                const Icon(Icons.flight_takeoff_rounded, color: AppColors.gold, size: 20),
                                const SizedBox(height: 4),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: AppColors.primary,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: const Text("Non-stop", style: TextStyle(color: AppColors.success, fontSize: 10)),
                                ),
                              ],
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text(f.arrivalTime, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                                Text(f.destinationCode, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                                Text(f.destinationCity, style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
                              ],
                            ),
                          ],
                        ),
                        const SizedBox(height: 14),
                        Row(
                          children: [
                            Expanded(
                              child: OutlinedButton(
                                onPressed: () {
                                  Navigator.of(context).push(
                                    MaterialPageRoute(
                                      builder: (_) => CheckoutScreen(
                                        title: "${f.airline} (${f.flightNumber}) ${f.originCode} ➔ ${f.destinationCode}",
                                        amount: f.priceUsd,
                                        serviceType: "flight",
                                      ),
                                    ),
                                  );
                                },
                                style: OutlinedButton.styleFrom(
                                  side: const BorderSide(color: AppColors.gold),
                                  foregroundColor: AppColors.gold,
                                ),
                                child: const Text("Book Flight"),
                              ),
                            ),
                          ],
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
