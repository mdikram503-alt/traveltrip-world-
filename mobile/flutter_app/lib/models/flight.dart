class Flight {
  final String id;
  final String airline;
  final String flightNumber;
  final String aircraft;
  final String originCity;
  final String originCode;
  final String destinationCity;
  final String destinationCode;
  final String departureTime;
  final String arrivalTime;
  final String duration;
  final String cabinClass;
  final double priceUsd;
  final String badge;
  final String bookingUrl;

  Flight({
    required this.id,
    required this.airline,
    required this.flightNumber,
    required this.aircraft,
    required this.originCity,
    required this.originCode,
    required this.destinationCity,
    required this.destinationCode,
    required this.departureTime,
    required this.arrivalTime,
    required this.duration,
    required this.cabinClass,
    required this.priceUsd,
    required this.badge,
    required this.bookingUrl,
  });

  factory Flight.fromJson(Map<String, dynamic> json) {
    final origin = json['origin'] as Map<String, dynamic>? ?? {};
    final dest = json['destination'] as Map<String, dynamic>? ?? {};

    return Flight(
      id: json['id'] ?? '',
      airline: json['airline'] ?? 'Premier Airline',
      flightNumber: json['flightNumber'] ?? '',
      aircraft: json['aircraft'] ?? '',
      originCity: origin['city'] ?? 'Dubai',
      originCode: origin['code'] ?? 'DXB',
      destinationCity: dest['city'] ?? 'London',
      destinationCode: dest['code'] ?? 'LHR',
      departureTime: json['departureTime'] ?? '08:00',
      arrivalTime: json['arrivalTime'] ?? '12:00',
      duration: json['duration'] ?? '7h',
      cabinClass: json['cabinClass'] ?? 'Economy',
      priceUsd: (json['priceUsd'] as num?)?.toDouble() ?? 450.0,
      badge: json['badge'] ?? 'Featured',
      bookingUrl: json['bookingUrl'] ?? 'https://traveltrip.world',
    );
  }
}
