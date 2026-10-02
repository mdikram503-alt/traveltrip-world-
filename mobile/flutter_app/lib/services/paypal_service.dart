import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import '../constants/config.dart';
import '../constants/theme.dart';

class PayPalConfig {
  static const String clientId = AppConfig.paypalClientId;
  static const String secretKey = AppConfig.paypalSecret;
}

class PayPalService {
  /// Opens in-app WebView for PayPal Checkout
  static Future<bool> openCheckout({
    required BuildContext context,
    required String approvalUrl,
    required String orderId,
  }) async {
    final result = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (ctx) => PayPalWebViewScreen(
          approvalUrl: approvalUrl,
          orderId: orderId,
        ),
      ),
    );
    return result ?? false;
  }
}

class PayPalWebViewScreen extends StatefulWidget {
  final String approvalUrl;
  final String orderId;

  const PayPalWebViewScreen({
    super.key,
    required this.approvalUrl,
    required this.orderId,
  });

  @override
  State<PayPalWebViewScreen> createState() => _PayPalWebViewScreenState();
}

class _PayPalWebViewScreenState extends State<PayPalWebViewScreen> {
  late final WebViewController _controller;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(AppColors.background)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (String url) {
            setState(() => _isLoading = true);
            _checkUrl(url);
          },
          onPageFinished: (String url) {
            setState(() => _isLoading = false);
            _checkUrl(url);
          },
          onNavigationRequest: (NavigationRequest request) {
            if (_checkUrl(request.url)) {
              return NavigationDecision.prevent;
            }
            return NavigationDecision.navigate;
          },
        ),
      )
      ..loadRequest(Uri.parse(widget.approvalUrl));
  }

  bool _checkUrl(String url) {
    // Check if redirect contains success tokens
    if (url.contains("return=success") ||
        url.contains("/checkout/success") ||
        url.contains("/api/checkout/capture") ||
        (url.contains("traveltrip.world") && url.contains("order_id="))) {
      Navigator.of(context).pop(true);
      return true;
    }
    // Check if user cancelled
    if (url.contains("cancel=true") || url.contains("/checkout/cancel")) {
      Navigator.of(context).pop(false);
      return true;
    }
    return false;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text("PayPal Checkout"),
        backgroundColor: AppColors.primary,
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context).pop(false),
        ),
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_isLoading)
            const Center(
              child: CircularProgressIndicator(color: AppColors.gold),
            ),
        ],
      ),
    );
  }
}
