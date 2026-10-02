import 'package:flutter/material.dart';
import '../constants/theme.dart';
import '../services/api_service.dart';

class AiPlannerScreen extends StatefulWidget {
  const AiPlannerScreen({super.key});

  @override
  State<AiPlannerScreen> createState() => _AiPlannerScreenState();
}

class _AiPlannerScreenState extends State<AiPlannerScreen> {
  final TextEditingController _destController = TextEditingController(text: "Dubai");
  int _selectedDays = 5;
  String _selectedBudget = "moderate";
  bool _isGenerating = false;
  Map<String, dynamic>? _itineraryResult;

  Future<void> _generatePlan() async {
    setState(() {
      _isGenerating = true;
      _itineraryResult = null;
    });

    final plan = await ApiService.generateAiItinerary(
      destination: _destController.text.trim(),
      days: _selectedDays,
      budget: _selectedBudget,
    );

    if (mounted) {
      setState(() {
        _itineraryResult = plan;
        _isGenerating = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text("AI Trip Planner"),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: const [
                        Icon(Icons.auto_awesome_rounded, color: AppColors.gold, size: 20),
                        SizedBox(width: 8),
                        Text("Personalized Travel AI Assistant", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      ],
                    ),
                    const SizedBox(height: 14),
                    TextField(
                      controller: _destController,
                      decoration: InputDecoration(
                        labelText: "Destination City / Country",
                        prefixIcon: const Icon(Icons.location_on_outlined, color: AppColors.gold),
                        filled: true,
                        fillColor: AppColors.primary,
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                    ),
                    const SizedBox(height: 14),
                    const Text("Trip Duration (Days)", style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [3, 5, 7, 10].map((d) {
                        final isSel = _selectedDays == d;
                        return ChoiceChip(
                          label: Text("$d Days"),
                          selected: isSel,
                          selectedColor: AppColors.gold,
                          backgroundColor: AppColors.primary,
                          labelStyle: TextStyle(
                            color: isSel ? AppColors.primary : AppColors.white,
                            fontWeight: FontWeight.bold,
                          ),
                          onSelected: (_) => setState(() => _selectedDays = d),
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 14),
                    const Text("Budget Style", style: TextStyle(color: AppColors.textSecondary, fontSize: 13)),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: ["budget", "moderate", "luxury"].map((b) {
                        final isSel = _selectedBudget == b;
                        return ChoiceChip(
                          label: Text(b.toUpperCase()),
                          selected: isSel,
                          selectedColor: AppColors.gold,
                          backgroundColor: AppColors.primary,
                          labelStyle: TextStyle(
                            color: isSel ? AppColors.primary : AppColors.white,
                            fontWeight: FontWeight.bold,
                            fontSize: 11,
                          ),
                          onSelected: (_) => setState(() => _selectedBudget = b),
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: _isGenerating ? null : _generatePlan,
                        icon: _isGenerating
                            ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary))
                            : const Icon(Icons.auto_awesome_rounded),
                        label: Text(_isGenerating ? "Crafting Itinerary..." : "Generate AI Itinerary"),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            if (_itineraryResult != null) ...[
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppColors.card,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.cardBorder),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          "${_itineraryResult!['destination']} ${_itineraryResult!['days']}-Day Guide",
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.gold),
                        ),
                        Text(
                          "Estimated Budget: ~\$${_itineraryResult!['suggestedBudgetUsd']} USD",
                          style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
                        ),
                      ],
                    ),
                    const Icon(Icons.check_circle_rounded, color: AppColors.success),
                  ],
                ),
              ),
              const SizedBox(height: 14),
              ...((_itineraryResult!['itinerary'] as List? ?? []).map((item) {
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item['title'] ?? 'Day Plan',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppColors.white),
                        ),
                        const SizedBox(height: 8),
                        _dayActivity("Morning", item['morning'] ?? ''),
                        const SizedBox(height: 6),
                        _dayActivity("Afternoon", item['afternoon'] ?? ''),
                        const SizedBox(height: 6),
                        _dayActivity("Evening", item['evening'] ?? ''),
                        const SizedBox(height: 8),
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: AppColors.primary,
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.wifi_rounded, size: 14, color: AppColors.success),
                              const SizedBox(width: 6),
                              Expanded(
                                child: Text(
                                  item['recommendedEsim'] ?? 'TravelTrip 5G eSIM connected.',
                                  style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              })),
            ],
          ],
        ),
      ),
    );
  }

  Widget _dayActivity(String time, String desc) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 70,
          child: Text(time, style: const TextStyle(color: AppColors.gold, fontSize: 12, fontWeight: FontWeight.bold)),
        ),
        Expanded(
          child: Text(desc, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
        ),
      ],
    );
  }
}
