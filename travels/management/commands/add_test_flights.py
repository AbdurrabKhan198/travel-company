import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from travels.models import Route, Schedule

class Command(BaseCommand):
    help = 'Add test flight data to the database'

    def handle(self, *args, **options):
        # List of major Indian cities with their airport codes
        cities = [
            ('Mumbai', 'BOM'),
            ('Delhi', 'DEL'),
            ('Bangalore', 'BLR'),
            ('Chennai', 'MAA'),
            ('Kolkata', 'CCU'),
            ('Hyderabad', 'HYD'),
            ('Pune', 'PNQ'),
            ('Goa', 'GOI'),
            ('Jaipur', 'JAI'),
            ('Kochi', 'COK'),
        ]

        # Generate unique carrier numbers
        used_carrier_numbers = set(Route.objects.values_list('carrier_number', flat=True))
        
        # Create routes between major cities
        for i in range(len(cities)):
            for j in range(i + 1, len(cities)):
                from_city, from_code = cities[i]
                to_city, to_code = cities[j]
                
                # Generate unique carrier numbers for this route
                while True:
                    carrier_number = f"AI{random.randint(100, 999)}"
                    if carrier_number not in used_carrier_numbers:
                        used_carrier_numbers.add(carrier_number)
                        break
                
                # Create route if it doesn't exist
                try:
                    route, created = Route.objects.get_or_create(
                        name=f"{from_code}-{to_code}",
                        defaults={
                            'from_location': from_city,
                            'to_location': to_city,
                            'transport_type': 'flight',
                            'carrier_number': carrier_number,
                            'departure_time': '09:00:00',
                            'arrival_time': '11:30:00',
                            'duration': timedelta(hours=2, minutes=30),
                            'route_type': 'domestic',
                            'base_price': 5000.00,
                            'amenities': {
                                'wifi': True,
                                'meals': True,
                                'entertainment': True,
                                'baggage': '15kg',
                            }
                        }
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating route {from_code}-{to_code}: {str(e)}'))
                    continue
                
                # Generate unique carrier number for return route
                while True:
                    return_carrier_number = f"AI{random.randint(100, 999)}"
                    if return_carrier_number not in used_carrier_numbers:
                        used_carrier_numbers.add(return_carrier_number)
                        break
                
                # Add return route
                try:
                    return_route, _ = Route.objects.get_or_create(
                        name=f"{to_code}-{from_code}",
                        defaults={
                            'from_location': to_city,
                            'to_location': from_city,
                            'transport_type': 'flight',
                            'carrier_number': return_carrier_number,
                            'departure_time': '14:00:00',
                            'arrival_time': '16:30:00',
                            'duration': timedelta(hours=2, minutes=30),
                            'route_type': 'domestic',
                            'base_price': 5000.00,
                            'amenities': {
                                'wifi': True,
                                'meals': True,
                                'entertainment': True,
                                'baggage': '15kg',
                            }
                        }
                    )
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error creating return route {to_code}-{from_code}: {str(e)}'))
                    continue

                # Create schedules for the next 30 days, skipping existing ones
                for day in range(1, 31):
                    try:
                        departure_date = timezone.now().date() + timedelta(days=day)
                        
                        # Check if schedule already exists for outbound flight
                        if not Schedule.objects.filter(route=route, departure_date=departure_date).exists():
                            Schedule.objects.create(
                                route=route,
                                departure_date=departure_date,
                                arrival_date=departure_date,
                                total_seats=180,
                                available_seats=random.randint(10, 180),
                                price=random.randint(3000, 10000),
                                notes=f"Flight {route.carrier_number} from {from_city} to {to_city}",
                                is_active=True
                            )
                            self.stdout.write(self.style.SUCCESS(f'Created schedule for {from_city} to {to_city} on {departure_date}'))

                        # Check if schedule already exists for return flight
                        return_date = departure_date + timedelta(days=random.randint(1, 7))
                        if not Schedule.objects.filter(route=return_route, departure_date=return_date).exists():
                            Schedule.objects.create(
                                route=return_route,
                                departure_date=return_date,
                                arrival_date=return_date,
                                total_seats=180,
                                available_seats=random.randint(10, 180),
                                price=random.randint(3000, 10000),
                                notes=f"Flight {return_route.carrier_number} from {to_city} to {from_city}",
                                is_active=True
                            )
                            self.stdout.write(self.style.SUCCESS(f'Created schedule for {to_city} to {from_city} on {return_date}'))
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error creating schedule: {str(e)}'))
                        continue

        self.stdout.write(self.style.SUCCESS('Successfully added test flight data!'))
