class Hotel {
  final String id;
  final String name;
  final String city;
  final String country;
  final double rating;
  final String stars;
  final double pricePerNightUsd;
  final String image;
  final List<String> amenities;
  final String bookingUrl;

  Hotel({
    required this.id,
    required this.name,
    required this.city,
    required this.country,
    required this.rating,
    required this.stars,
    required this.pricePerNightUsd,
    required this.image,
    required this.amenities,
    required this.bookingUrl,
  });

  factory Hotel.fromJson(Map<String, dynamic> json) {
    return Hotel(
      id: json['id'] ?? '',
      name: json['name'] ?? 'Luxury Resort',
      city: json['city'] ?? 'Dubai',
      country: json['country'] ?? 'UAE',
      rating: (json['rating'] as num?)?.toDouble() ?? 4.8,
      stars: json['stars'] ?? '5-Star',
      pricePerNightUsd: (json['pricePerNightUsd'] as num?)?.toDouble() ?? 250.0,
      image: json['image'] ?? '/images/dubai.jpg',
      amenities: List<String>.from(json['amenities'] ?? []),
      bookingUrl: json['bookingUrl'] ?? 'https://traveltrip.world',
    );
  }
}
