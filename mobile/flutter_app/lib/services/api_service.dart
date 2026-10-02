import 'dart:convert';
import 'package:http/http.dart' as http;
import '../constants/config.dart';
import '../models/esim_package.dart';
import '../models/flight.dart';
import '../models/hotel.dart';

class ApiService {
  static final http.Client _client = http.Client();

  /// Create Stripe Payment Intent for in-app Stripe PaymentSheet
  static Future<Map<String, dynamic>?> createPaymentIntent({
    double? amount,
    String? packageCode,
    String? buyerEmail,
    String? buyerName,
    String? locationCode,
  }) async {
    try {
      final url = Uri.parse("${AppConfig.baseUrl}${AppConfig.endpointCreatePaymentIntent}");
      final body = {
        if (amount != null) "amount": amount,
        if (packageCode != null) "packageCode": packageCode,
        "buyerEmail": buyerEmail ?? "guest@traveltrip.world",
        "buyerName": buyerName ?? "Traveler Customer",
        "locationCode": locationCode ?? "GLOBAL",
        "currency": "usd",
      };

      final response = await _client.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(body),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        print("[API ERROR] createPaymentIntent status ${response.statusCode}: ${response.body}");
        return null;
      }
    } catch (e) {
      print("[API EXCEPTION] createPaymentIntent: $e");
      return null;
    }
  }

  /// Create PayPal Order returning approval_url for in-app WebView
  static Future<Map<String, dynamic>?> createPaypalOrder({
    double? amount,
    String? packageCode,
    String? buyerEmail,
    String? buyerName,
    String? locationCode,
  }) async {
    try {
      final url = Uri.parse("${AppConfig.baseUrl}${AppConfig.endpointCreatePaypalOrder}");
      final body = {
        if (amount != null) "amount": amount,
        if (packageCode != null) "packageCode": packageCode,
        "buyerEmail": buyerEmail ?? "guest@traveltrip.world",
        "buyerName": buyerName ?? "Traveler Customer",
        "locationCode": locationCode ?? "GLOBAL",
      };

      final response = await _client.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode(body),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        print("[API ERROR] createPaypalOrder status ${response.statusCode}: ${response.body}");
        return null;
      }
    } catch (e) {
      print("[API EXCEPTION] createPaypalOrder: $e");
      return null;
    }
  }

  /// Fetch Wholesale eSIM catalog
  static Future<List<EsimPackage>> fetchPackages({String locationCode = ""}) async {
    try {
      final url = Uri.parse("${AppConfig.baseUrl}${AppConfig.endpointPackages}${locationCode.isNotEmpty ? '?cc=$locationCode' : ''}");
      final response = await _client.get(url);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final List<EsimPackage> list = [];
        if (data is Map && data['packages'] is Map) {
          final pkgMap = data['packages'] as Map<String, dynamic>;
          pkgMap.forEach((cc, items) {
            if (items is List) {
              for (var item in items) {
                list.add(EsimPackage.fromJson(item, countryCode: cc));
              }
            }
          });
        }
        return list;
      }
    } catch (e) {
      print("[API EXCEPTION] fetchPackages: $e");
    }
    return [];
  }

  /// Fetch curated premier flights
  static Future<List<Flight>> fetchFlights() async {
    try {
      final url = Uri.parse("${AppConfig.baseUrl}${AppConfig.endpointFlights}");
      final response = await _client.get(url);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['flights'] is List) {
          return (data['flights'] as List).map((f) => Flight.fromJson(f)).toList();
        }
      }
    } catch (e) {
      print("[API EXCEPTION] fetchFlights: $e");
    }
    return [];
  }

  /// Fetch luxury & curated hotels
  static Future<List<Hotel>> fetchHotels() async {
    try {
      final url = Uri.parse("${AppConfig.baseUrl}${AppConfig.endpointHotels}");
      final response = await _client.get(url);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['hotels'] is List) {
          return (data['hotels'] as List).map((h) => Hotel.fromJson(h)).toList();
        }
      }
    } catch (e) {
      print("[API EXCEPTION] fetchHotels: $e");
    }
    return [];
  }

  /// Fetch visa guidelines
  static Future<List<Map<String, dynamic>>> fetchVisaList() async {
    try {
      final url = Uri.parse("${AppConfig.baseUrl}${AppConfig.endpointVisa}");
      final response = await _client.get(url);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['visas'] is List) {
          return List<Map<String, dynamic>>.from(data['visas']);
        }
      }
    } catch (e) {
      print("[API EXCEPTION] fetchVisaList: $e");
    }
    return [];
  }

  /// Fetch wallet info
  static Future<Map<String, dynamic>?> fetchWallet() async {
    try {
      final url = Uri.parse("${AppConfig.baseUrl}${AppConfig.endpointWallet}");
      final response = await _client.get(url);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['wallet'] as Map<String, dynamic>?;
      }
    } catch (e) {
      print("[API EXCEPTION] fetchWallet: $e");
    }
    return null;
  }

  /// Fetch VIP tiers
  static Future<List<Map<String, dynamic>>> fetchVipTiers() async {
    try {
      final url = Uri.parse("${AppConfig.baseUrl}${AppConfig.endpointVip}");
      final response = await _client.get(url);
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['tiers'] is List) {
          return List<Map<String, dynamic>>.from(data['tiers']);
        }
      }
    } catch (e) {
      print("[API EXCEPTION] fetchVipTiers: $e");
    }
    return [];
  }

  /// Generate AI Trip Itinerary
  static Future<Map<String, dynamic>?> generateAiItinerary({
    required String destination,
    int days = 5,
    String budget = "moderate",
    String style = "luxury & adventure",
  }) async {
    try {
      final url = Uri.parse("${AppConfig.baseUrl}${AppConfig.endpointAiPlanner}");
      final response = await _client.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "destination": destination,
          "days": days,
          "budget": budget,
          "style": style,
        }),
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (e) {
      print("[API EXCEPTION] generateAiItinerary: $e");
    }
    return null;
  }
}
