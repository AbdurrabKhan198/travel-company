from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from travels.models import Route, Inventory, Package
from datetime import date, timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate database with sample data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating sample data...')
        
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@safarzone.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('[OK] Admin user created (username: admin, password: admin123)'))
        
        # Create regular user
        if not User.objects.filter(username='testuser').exists():
            User.objects.create_user('testuser', 'user@example.com', 'test123')
            self.stdout.write(self.style.SUCCESS('[OK] Test user created (username: testuser, password: test123)'))
        
        # Create Routes (domestic + international) with base prices
        routes_data = [
            # Domestic
            {'flight_number': 'SZ101', 'from_location': 'Mumbai', 'to_location': 'Delhi', 'duration': '2h 15m', 'route_type': 'domestic', 'base_price': 3500},
            {'flight_number': 'SZ202', 'from_location': 'Delhi', 'to_location': 'Mumbai', 'duration': '2h 20m', 'route_type': 'domestic', 'base_price': 4200},
            {'flight_number': 'SZ303', 'from_location': 'Mumbai', 'to_location': 'Bangalore', 'duration': '1h 45m', 'route_type': 'domestic', 'base_price': 5000},
            {'flight_number': 'SZ404', 'from_location': 'Bangalore', 'to_location': 'Mumbai', 'duration': '1h 50m', 'route_type': 'domestic', 'base_price': 3800},
            {'flight_number': 'SZ505', 'from_location': 'Delhi', 'to_location': 'Goa', 'duration': '2h 30m', 'route_type': 'domestic', 'base_price': 6500},
            {'flight_number': 'SZ606', 'from_location': 'Goa', 'to_location': 'Delhi', 'duration': '2h 35m', 'route_type': 'domestic', 'base_price': 4800},
            {'flight_number': 'SZ707', 'from_location': 'Mumbai', 'to_location': 'Kolkata', 'duration': '2h 50m', 'route_type': 'domestic', 'base_price': 5200},
            {'flight_number': 'SZ808', 'from_location': 'Kolkata', 'to_location': 'Mumbai', 'duration': '2h 55m', 'route_type': 'domestic', 'base_price': 4500},
            {'flight_number': 'SZ909', 'from_location': 'Chennai', 'to_location': 'Delhi', 'duration': '3h 10m', 'route_type': 'domestic', 'base_price': 5800},
            {'flight_number': 'SZ1010', 'from_location': 'Delhi', 'to_location': 'Chennai', 'duration': '3h 05m', 'route_type': 'domestic', 'base_price': 4000},
            # International
            {'flight_number': 'SZI11', 'from_location': 'Mumbai', 'to_location': 'Dubai', 'duration': '3h 30m', 'route_type': 'international', 'base_price': 22000},
            {'flight_number': 'SZI12', 'from_location': 'Delhi', 'to_location': 'Dubai', 'duration': '3h 20m', 'route_type': 'international', 'base_price': 21000},
            {'flight_number': 'SZI21', 'from_location': 'Mumbai', 'to_location': 'Singapore', 'duration': '5h 30m', 'route_type': 'international', 'base_price': 35000},
            {'flight_number': 'SZI31', 'from_location': 'Delhi', 'to_location': 'London', 'duration': '9h 00m', 'route_type': 'international', 'base_price': 65000},
            {'flight_number': 'SZI41', 'from_location': 'Bangalore', 'to_location': 'Bangkok', 'duration': '3h 55m', 'route_type': 'international', 'base_price': 24000},
        ]

        routes_with_price = []
        for rd in routes_data:
            base_price = rd.pop('base_price')
            route_fields = rd
            route, created = Route.objects.get_or_create(
                flight_number=route_fields['flight_number'],
                defaults=route_fields
            )
            # If route existed but route_type changed, update it
            if not created:
                updated = False
                for key in ['from_location', 'to_location', 'duration', 'route_type']:
                    if getattr(route, key) != route_fields[key]:
                        setattr(route, key, route_fields[key])
                        updated = True
                if updated:
                    route.save()
            routes_with_price.append((route, base_price))
            if created:
                self.stdout.write(f'  Created route: {route.flight_number}')

        self.stdout.write(self.style.SUCCESS(f'[OK] {len(routes_with_price)} routes created/verified'))

        # Create Inventory (available dates for next 30 days)
        today = date.today()

        inventory_count = 0
        for route, base_price in routes_with_price:
            for days_ahead in [3, 7, 10, 14, 21, 28]:
                travel_date = today + timedelta(days=days_ahead)
                inv, created = Inventory.objects.get_or_create(
                    route=route,
                    travel_date=travel_date,
                    defaults={
                        'total_seats': 180,
                        'available_seats': 180,
                        'price': Decimal(str(base_price)),
                        'is_active': True
                    }
                )
                if created:
                    inventory_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'[OK] {inventory_count} inventory items created'))
        
        # Create Travel Packages
        packages_data = [
            {
                'destination': 'Goa',
                'title': 'Beach Paradise - Goa Special',
                'description': 'Experience the beautiful beaches of Goa with our exclusive 5-day package. Includes hotel stay, breakfast, and sightseeing tours to famous beaches and churches.',
                'price': Decimal('25000'),
                'duration': '5 Days 4 Nights',
                'image_url': 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800',
                'is_featured': True
            },
            {
                'destination': 'Kerala',
                'title': 'Gods Own Country - Kerala Tour',
                'description': 'Explore the backwaters, hill stations, and tea plantations of Kerala. Includes houseboat stay, Munnar visit, and Ayurvedic spa treatments.',
                'price': Decimal('32000'),
                'duration': '6 Days 5 Nights',
                'image_url': 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800',
                'is_featured': True
            },
            {
                'destination': 'Rajasthan',
                'title': 'Royal Rajasthan Heritage Tour',
                'description': 'Visit the majestic forts and palaces of Rajasthan. Includes Jaipur, Udaipur, and Jodhpur with heritage hotel stays and camel safari.',
                'price': Decimal('45000'),
                'duration': '7 Days 6 Nights',
                'image_url': 'https://images.unsplash.com/photo-1524230572899-a752b3835840?w=800',
                'is_featured': True
            },
            {
                'destination': 'Himachal Pradesh',
                'title': 'Mountain Escape - Shimla & Manali',
                'description': 'Breathtaking views of the Himalayas with adventure activities. Includes trekking, paragliding, river rafting, and visits to scenic valleys.',
                'price': Decimal('28000'),
                'duration': '5 Days 4 Nights',
                'image_url': 'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800',
                'is_featured': True
            },
            {
                'destination': 'Dubai',
                'title': 'Luxury Dubai Experience',
                'description': 'Experience luxury in Dubai with Burj Khalifa, desert safari, luxury shopping, and world-class dining experiences.',
                'price': Decimal('65000'),
                'duration': '4 Days 3 Nights',
                'image_url': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800',
                'is_featured': True
            },
            {
                'destination': 'Maldives',
                'title': 'Tropical Paradise - Maldives',
                'description': 'Relax in overwater bungalows with crystal clear waters. Includes all meals, water sports, and spa treatments.',
                'price': Decimal('85000'),
                'duration': '5 Days 4 Nights',
                'image_url': 'https://images.unsplash.com/photo-1514282401047-d79a71a590e8?w=800',
                'is_featured': True
            },
        ]
        
        package_count = 0
        for pkg_data in packages_data:
            pkg, created = Package.objects.get_or_create(
                destination=pkg_data['destination'],
                title=pkg_data['title'],
                defaults=pkg_data
            )
            if created:
                package_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'[OK] {package_count} travel packages created'))
        
        self.stdout.write(self.style.SUCCESS('\n=== Sample Data Population Complete! ==='))
        self.stdout.write(self.style.SUCCESS('You can now login with:'))
        self.stdout.write('  Admin: username=admin, password=admin123')
        self.stdout.write('  User: username=testuser, password=test123')
