import 'package:flutter/material.dart';
import '../constants/theme.dart';
import '../services/stripe_service.dart';
import '../services/paypal_service.dart';
import '../services/api_service.dart';

class CheckoutScreen extends StatefulWidget {
  final String title;
  final String? packageCode;
  final double amount;
  final String serviceType; // esim, flight, hotel, visa, tour, wallet

  const CheckoutScreen({
    super.key,
    required this.title,
    this.packageCode,
    required this.amount,
    this.serviceType = "general",
  });

  @override
  State<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends State<CheckoutScreen> {
  final TextEditingController _emailController = TextEditingController(text: "customer@traveltrip.world");
  final TextEditingController _nameController = TextEditingController(text: "Traveler Customer");
  bool _isProcessing = false;
  String? _statusMessage;

  Future<void> _handleStripePayment() async {
    setState(() {
      _isProcessing = true;
      _statusMessage = "Connecting to Stripe Secure Gateway...";
    });

    final res = await ApiService.createPaymentIntent(
      amount: widget.amount,
      packageCode: widget.packageCode,
      buyerEmail: _emailController.text.trim(),
      buyerName: _nameController.text.trim(),
    );

    if (res == null || res['clientSecret'] == null) {
      setState(() {
        _isProcessing = false;
        _statusMessage = res?['error'] ?? "Failed to initialize Stripe Payment Sheet.";
      });
      return;
    }

    final clientSecret = res['clientSecret'] as String;
    setState(() => _statusMessage = "Presenting Stripe Payment Sheet...");

    final success = await StripeService.makePayment(clientSecret: clientSecret);

    setState(() => _isProcessing = false);

    if (success) {
      _showSuccessDialog("Stripe Payment Successful!", "Order ID: ${res['orderId'] ?? 'TRIP-CONFIRMED'}");
    } else {
      setState(() => _statusMessage = "Payment was not completed.");
    }
  }

  Future<void> _handlePayPalPayment() async {
    setState(() {
      _isProcessing = true;
      _statusMessage = "Creating PayPal Order...";
    });

    final res = await ApiService.createPaypalOrder(
      amount: widget.amount,
      packageCode: widget.packageCode,
      buyerEmail: _emailController.text.trim(),
      buyerName: _nameController.text.trim(),
    );

    if (res == null || res['approval_url'] == null) {
      setState(() {
        _isProcessing = false;
        _statusMessage = res?['error'] ?? "Failed to initialize PayPal Checkout.";
      });
      return;
    }

    final approvalUrl = res['approval_url'] as String;
    final orderId = res['orderId'] ?? res['id'] ?? "ORDER";

    setState(() {
      _isProcessing = false;
      _statusMessage = null;
    });

    if (mounted) {
      final success = await PayPalService.openCheckout(
        context: context,
        approvalUrl: approvalUrl,
        orderId: orderId,
      );

      if (success) {
        _showSuccessDialog("PayPal Order Confirmed!", "Transaction completed for Order ID: $orderId");
      }
    }
  }

  void _showSuccessDialog(String title, String message) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.card,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Row(
          children: [
            const Icon(Icons.check_circle_rounded, color: AppColors.success, size: 28),
            const SizedBox(width: 8),
            Text(title, style: const TextStyle(color: AppColors.white, fontSize: 18)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(message, style: const TextStyle(color: AppColors.textSecondary, fontSize: 14)),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppColors.cardBorder),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("Item: ${widget.title}", style: const TextStyle(color: AppColors.white, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  Text("Paid: \$${widget.amount.toStringAsFixed(2)} USD", style: const TextStyle(color: AppColors.gold)),
                  const SizedBox(height: 4),
                  Text("Receipt sent to: ${_emailController.text}", style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                ],
              ),
            ),
          ],
        ),
        actions: [
          ElevatedButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              Navigator.of(context).pop(true);
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.gold),
            child: const Text("Done", style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text("Secure Checkout"),
        backgroundColor: AppColors.primary,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Order Summary Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text("Order Summary", style: TextStyle(fontSize: 14, color: AppColors.textSecondary)),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: AppColors.gold.withOpacity(0.15),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            widget.serviceType.toUpperCase(),
                            style: const TextStyle(color: AppColors.gold, fontSize: 11, fontWeight: FontWeight.bold),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      widget.title,
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.white),
                    ),
                    const Divider(height: 28, color: AppColors.cardBorder),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text("Total Payable", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                        Text(
                          "\$${widget.amount.toStringAsFixed(2)} USD",
                          style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: AppColors.gold),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            // Contact Info
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text("Traveler Details", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 14),
                    TextField(
                      controller: _nameController,
                      decoration: InputDecoration(
                        labelText: "Full Name",
                        prefixIcon: const Icon(Icons.person_outline, color: AppColors.gold),
                        filled: true,
                        fillColor: AppColors.primary,
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      decoration: InputDecoration(
                        labelText: "Delivery Email (for eSIM QR / E-Ticket)",
                        prefixIcon: const Icon(Icons.email_outlined, color: AppColors.gold),
                        filled: true,
                        fillColor: AppColors.primary,
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 24),

            if (_statusMessage != null)
              Container(
                padding: const EdgeInsets.all(12),
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: AppColors.card,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.accentCyan),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.info_outline, color: AppColors.accentCyan, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _statusMessage!,
                        style: const TextStyle(color: AppColors.white, fontSize: 13),
                      ),
                    ),
                  ],
                ),
              ),

            // Payment Buttons
            if (_isProcessing)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(16.0),
                  child: CircularProgressIndicator(color: AppColors.gold),
                ),
              )
            else
              Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Stripe Button
                  ElevatedButton.icon(
                    onPressed: _handleStripePayment,
                    icon: const Icon(Icons.credit_card_rounded, color: AppColors.primary),
                    label: const Text("Pay with Stripe (Cards & Apple/Google Pay)"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.gold,
                      foregroundColor: AppColors.primary,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                  ),

                  const SizedBox(height: 14),

                  // PayPal Button
                  ElevatedButton.icon(
                    onPressed: _handlePayPalPayment,
                    icon: const Icon(Icons.account_balance_wallet_rounded, color: Colors.white),
                    label: const Text("Pay with PayPal"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF0070BA),
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                  ),
                ],
              ),

            const SizedBox(height: 18),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: const [
                Icon(Icons.lock_rounded, size: 14, color: AppColors.textMuted),
                SizedBox(width: 6),
                Text(
                  "256-Bit SSL Encrypted • Official Stripe & PayPal Gateways",
                  style: TextStyle(color: AppColors.textMuted, fontSize: 11),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
