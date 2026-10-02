import 'package:flutter/material.dart';
import '../constants/theme.dart';
import '../services/api_service.dart';
import 'checkout_screen.dart';

class VisaScreen extends StatefulWidget {
  const VisaScreen({super.key});

  @override
  State<VisaScreen> createState() => _VisaScreenState();
}

class _VisaScreenState extends State<VisaScreen> {
  List<Map<String, dynamic>> _visaList = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadVisas();
  }

  Future<void> _loadVisas() async {
    final list = await ApiService.fetchVisaList();
    if (mounted) {
      setState(() {
        _visaList = list;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text("Visa Processing & Services"),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: AppColors.gold))
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _visaList.length,
              itemBuilder: (ctx, i) {
                final v = _visaList[i];
                final docs = List<String>.from(v['documentsRequired'] ?? []);
                final fee = (v['feeUsd'] as num?)?.toDouble() ?? 100.0;

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
                            Text(
                              v['country'] ?? 'Visa Service',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17, color: AppColors.gold),
                            ),
                            Text(
                              "\$${fee.toStringAsFixed(0)} USD",
                              style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 18, color: AppColors.white),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            const Icon(Icons.timer_outlined, size: 14, color: AppColors.accentCyan),
                            const SizedBox(width: 4),
                            Text("Processing: ${v['processingTime'] ?? '2-3 days'}", style: const TextStyle(color: AppColors.accentCyan, fontSize: 12)),
                          ],
                        ),
                        const SizedBox(height: 12),
                        const Text("Required Documents:", style: TextStyle(color: AppColors.textSecondary, fontSize: 12, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 6),
                        ...docs.map((d) => Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(Icons.check_circle_outline_rounded, size: 14, color: AppColors.success),
                              const SizedBox(width: 6),
                              Expanded(child: Text(d, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary))),
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
                                    title: "${v['country']} Visa Application Service",
                                    amount: fee,
                                    serviceType: "visa",
                                  ),
                                ),
                              );
                            },
                            child: const Text("Apply Online • Fast Track"),
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
