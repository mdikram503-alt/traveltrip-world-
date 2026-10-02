class EsimPackage {
  final String packageCode;
  final String name;
  final String data;
  final String validity;
  final String network;
  final double priceUsd;
  final bool unlimited;
  final String countryCode;

  EsimPackage({
    required this.packageCode,
    required this.name,
    required this.data,
    required this.validity,
    required this.network,
    required this.priceUsd,
    required this.unlimited,
    this.countryCode = "GLOBAL",
  });

  factory EsimPackage.fromJson(Map<String, dynamic> json, {String countryCode = "GLOBAL"}) {
    double parsePrice(dynamic val) {
      if (val is num) return val.toDouble();
      if (val is String) {
        return double.tryParse(val.replaceAll(RegExp(r'[^0-9.]'), '')) ?? 0.0;
      }
      return 0.0;
    }

    return EsimPackage(
      packageCode: json['packageCode'] ?? json['code'] ?? '',
      name: json['name'] ?? 'eSIM Plan',
      data: json['data'] ?? '1 GB',
      validity: json['validity'] ?? '7 Days',
      network: json['network'] ?? '5G / 4G LTE High-Speed',
      priceUsd: parsePrice(json['priceUsd'] ?? json['price'] ?? 0.0),
      unlimited: json['unlimited'] == true,
      countryCode: json['countryCode'] ?? countryCode,
    );
  }
}
