from django.core.management.base import BaseCommand
from django.utils import timezone
from travels.models import Route, Schedule
from datetime import datetime, timedelta, time
from decimal import Decimal

class Command(BaseCommand):
    help = 'Add comprehensive test flights including Delhi to Dubai and other popular routes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating test flights...'))
        
        # Popular routes with realistic data
        routes_data = [
            # Domestic Routes
            {'from': 'Delhi', 'to': 'Mumbai', 'carrier': 'AI101', 'dep_time': '08:00', 'duration_h': 2, 'duration_m': 30, 'price': 5000, 'type': 'domestic'},
            {'from': 'Mumbai', 'to': 'Delhi', 'carrier': 'AI102', 'dep_time': '11:00', 'duration_h': 2, 'duration_m': 30, 'price': 5000, 'type': 'domestic'},
            {'from': 'Delhi', 'to': 'Bangalore', 'carrier': 'AI201', 'dep_time': '09:00', 'duration_h': 2, 'duration_m': 45, 'price': 5500, 'type': 'domestic'},
            {'from': 'Bangalore', 'to': 'Delhi', 'carrier': 'AI202', 'dep_time': '12:00', 'duration_h': 2, 'duration_m': 45, 'price': 5500, 'type': 'domestic'},
            {'from': 'Mumbai', 'to': 'Bangalore', 'carrier': 'AI301', 'dep_time': '10:00', 'duration_h': 1, 'duration_m': 45, 'price': 4500, 'type': 'domestic'},
            {'from': 'Bangalore', 'to': 'Mumbai', 'carrier': 'AI302', 'dep_time': '13:00', 'duration_h': 1, 'duration_m': 45, 'price': 4500, 'type': 'domestic'},
            {'from': 'Delhi', 'to': 'Chennai', 'carrier': 'AI401', 'dep_time': '07:30', 'duration_h': 2, 'duration_m': 30, 'price': 5200, 'type': 'domestic'},
            {'from': 'Chennai', 'to': 'Delhi', 'carrier': 'AI402', 'dep_time': '10:30', 'duration_h': 2, 'duration_m': 30, 'price': 5200, 'type': 'domestic'},
            {'from': 'Mumbai', 'to': 'Goa', 'carrier': 'AI501', 'dep_time': '06:00', 'duration_h': 1, 'duration_m': 15, 'price': 3500, 'type': 'domestic'},
            {'from': 'Goa', 'to': 'Mumbai', 'carrier': 'AI502', 'dep_time': '08:00', 'duration_h': 1, 'duration_m': 15, 'price': 3500, 'type': 'domestic'},
            
            # International Routes (including Delhi to Dubai)
            {'from': 'Delhi', 'to': 'Dubai', 'carrier': 'EK701', 'dep_time': '22:00', 'duration_h': 3, 'duration_m': 30, 'price': 20000, 'type': 'international'},
            {'from': 'Dubai', 'to': 'Delhi', 'carrier': 'EK702', 'dep_time': '02:30', 'duration_h': 3, 'duration_m': 30, 'price': 20000, 'type': 'international'},
            {'from': 'Mumbai', 'to': 'Dubai', 'carrier': 'EK601', 'dep_time': '21:30', 'duration_h': 3, 'duration_m': 0, 'price': 18000, 'type': 'international'},
            {'from': 'Dubai', 'to': 'Mumbai', 'carrier': 'EK602', 'dep_time': '01:30', 'duration_h': 3, 'duration_m': 0, 'price': 18000, 'type': 'international'},
            {'from': 'Delhi', 'to': 'Singapore', 'carrier': 'SQ101', 'dep_time': '23:30', 'duration_h': 5, 'duration_m': 30, 'price': 25000, 'type': 'international'},
            {'from': 'Singapore', 'to': 'Delhi', 'carrier': 'SQ102', 'dep_time': '01:30', 'duration_h': 5, 'duration_m': 30, 'price': 25000, 'type': 'international'},
            {'from': 'Mumbai', 'to': 'Singapore', 'carrier': 'SQ201', 'dep_time': '22:00', 'duration_h': 5, 'duration_m': 0, 'price': 23000, 'type': 'international'},
            {'from': 'Singapore', 'to': 'Mumbai', 'carrier': 'SQ202', 'dep_time': '00:00', 'duration_h': 5, 'duration_m': 0, 'price': 23000, 'type': 'international'},
            {'from': 'Delhi', 'to': 'Bangkok', 'carrier': 'TG301', 'dep_time': '10:00', 'duration_h': 4, 'duration_m': 0, 'price': 22000, 'type': 'international'},
            {'from': 'Bangkok', 'to': 'Delhi', 'carrier': 'TG302', 'dep_time': '14:00', 'duration_h': 4, 'duration_m': 0, 'price': 22000, 'type': 'international'},
        ]
        
        today = timezone.now().date()
        routes_created = 0
        schedules_created = 0
        
        for route_data in routes_data:
            # Parse departure time
            dep_time_parts = route_data['dep_time'].split(':')
            dep_time = time(int(dep_time_parts[0]), int(dep_time_parts[1]))
            
            # Calculate arrival time
            duration = timedelta(hours=route_data['duration_h'], minutes=route_data['duration_m'])
            dep_datetime = datetime.combine(today, dep_time)
            arr_datetime = dep_datetime + duration
            arr_time = arr_datetime.time()
            
            # Create route name
            route_name = f"{route_data['from']} to {route_data['to']}"
            
            # Get or create route using carrier_number (which is unique)
            route, created = Route.objects.get_or_create(
                carrier_number=route_data['carrier'],
                defaults={
                    'name': route_name,
                    'from_location': route_data['from'],
                    'to_location': route_data['to'],
                    'transport_type': 'flight',
                    'departure_time': dep_time,
                    'arrival_time': arr_time,
                    'duration': duration,
                    'route_type': route_data['type'],
                    'base_price': Decimal(str(route_data['price'])),
                    'is_active': True,
                    'description': f"Flight from {route_data['from']} to {route_data['to']}",
                    'amenities': {
                        'wifi': True,
                        'meals': True,
                        'entertainment': True,
                        'baggage': '15kg' if route_data['type'] == 'domestic' else '20kg',
                    }
                }
            )
            
            if created:
                routes_created += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created route: {route_name} ({route_data["carrier"]})'))
            else:
                self.stdout.write(self.style.WARNING(f'→ Route already exists: {route_name}'))
            
            # Create schedules for next 60 days
            for day in range(60):
                departure_date = today + timedelta(days=day)
                
                # Skip if schedule already exists
                if Schedule.objects.filter(route=route, departure_date=departure_date).exists():
                    continue
                
                # Calculate arrival date (might be next day for late night flights)
                arrival_date = departure_date
                if dep_time.hour >= 22:  # Late night flights arrive next day
                    arrival_date = departure_date + timedelta(days=1)
                
                # Random available seats (between 20 and total_seats)
                total_seats = 180
                available_seats = 180 - (day % 50)  # Varying availability
                
                # Price variation (±10%)
                price_variation = Decimal(str(route_data['price'])) * Decimal('0.1')
                price = Decimal(str(route_data['price'])) + (price_variation * Decimal(str((day % 20) - 10)) / Decimal('10'))
                
                schedule = Schedule.objects.create(
                    route=route,
                    departure_date=departure_date,
                    arrival_date=arrival_date,
                    total_seats=total_seats,
                    available_seats=available_seats,
                    price=price,
                    is_active=True,
                    notes=f"Flight {route_data['carrier']} on {departure_date.strftime('%Y-%m-%d')}"
                )
                schedules_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created:'))
        self.stdout.write(self.style.SUCCESS(f'   • {routes_created} new routes'))
        self.stdout.write(self.style.SUCCESS(f'   • {schedules_created} flight schedules'))
        self.stdout.write(self.style.SUCCESS(f'\n🎉 Test flights are ready! You can now search for flights.'))
        self.stdout.write(self.style.SUCCESS(f'\n💡 Try searching: Delhi → Dubai (International)'))

