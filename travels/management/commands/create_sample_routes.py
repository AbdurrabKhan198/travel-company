from django.core.management.base import BaseCommand
from django.utils import timezone
from travels.models import Route, Schedule
from datetime import datetime, time, timedelta

class Command(BaseCommand):
    help = 'Creates sample flight routes and schedules'

    def handle(self, *args, **options):
        def create_duration(hours, minutes=0, seconds=0):
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
            
        # Domestic routes
        domestic_routes = [
            {'from_location': 'Mumbai', 'to_location': 'Delhi', 'carrier_number': 'AI101', 'departure_time': '08:00:00', 'duration': create_duration(2, 30), 'base_price': 5000},
            {'from_location': 'Delhi', 'to_location': 'Mumbai', 'carrier_number': 'AI102', 'departure_time': '11:00:00', 'duration': create_duration(2, 30), 'base_price': 5000},
            {'from_location': 'Bangalore', 'to_location': 'Mumbai', 'carrier_number': 'AI201', 'departure_time': '09:30:00', 'duration': create_duration(1, 45), 'base_price': 4500},
            {'from_location': 'Mumbai', 'to_location': 'Bangalore', 'carrier_number': 'AI202', 'departure_time': '12:30:00', 'duration': create_duration(1, 45), 'base_price': 4500},
            {'from_location': 'Delhi', 'to_location': 'Bangalore', 'carrier_number': 'AI301', 'departure_time': '10:00:00', 'duration': create_duration(2, 45), 'base_price': 5500},
            {'from_location': 'Bangalore', 'to_location': 'Delhi', 'carrier_number': 'AI302', 'departure_time': '13:00:00', 'duration': create_duration(2, 45), 'base_price': 5500},
        ]
        
        # International routes
        international_routes = [
            {'from_location': 'Mumbai', 'to_location': 'Dubai', 'carrier_number': 'EK501', 'departure_time': '22:00:00', 'duration': create_duration(3, 30), 'base_price': 20000},
            {'from_location': 'Dubai', 'to_location': 'Mumbai', 'carrier_number': 'EK502', 'departure_time': '02:30:00', 'duration': create_duration(3, 30), 'base_price': 20000},
            {'from_location': 'Delhi', 'to_location': 'Singapore', 'carrier_number': 'SQ101', 'departure_time': '23:30:00', 'duration': create_duration(5, 30), 'base_price': 25000},
            {'from_location': 'Singapore', 'to_location': 'Delhi', 'carrier_number': 'SQ102', 'departure_time': '01:30:00', 'duration': create_duration(5, 30), 'base_price': 25000},
        ]

        # Create routes
        for route_data in domestic_routes:
            route, created = Route.objects.get_or_create(
                name=f"{route_data['from_location']} to {route_data['to_location']}",
                from_location=route_data['from_location'],
                to_location=route_data['to_location'],
                defaults={
                    'transport_type': 'flight',
                    'carrier_number': route_data['carrier_number'],
                    'departure_time': route_data['departure_time'],
                    'arrival_time': (datetime.strptime(route_data['departure_time'], '%H:%M:%S') + route_data['duration']).strftime('%H:%M:%S'),
                    'duration': route_data['duration'],
                    'route_type': 'domestic',
                    'base_price': route_data['base_price'],
                    'is_active': True,
                    'description': f"Daily flight from {route_data['from_location']} to {route_data['to_location']}",
                    'amenities': {"wifi": True, "meals": True, "entertainment": True}
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created route: {route}'))

        for route_data in international_routes:
            route, created = Route.objects.get_or_create(
                name=f"{route_data['from_location']} to {route_data['to_location']}",
                from_location=route_data['from_location'],
                to_location=route_data['to_location'],
                defaults={
                    'transport_type': 'flight',
                    'carrier_number': route_data['carrier_number'],
                    'departure_time': route_data['departure_time'],
                    'arrival_time': (datetime.strptime(route_data['departure_time'], '%H:%M:%S') + route_data['duration']).strftime('%H:%M:%S'),
                    'duration': route_data['duration'],
                    'route_type': 'international',
                    'base_price': route_data['base_price'],
                    'is_active': True,
                    'description': f"Daily international flight from {route_data['from_location']} to {route_data['to_location']}",
                    'amenities': {"wifi": True, "meals": True, "entertainment": True, "usb_ports": True}
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created international route: {route}'))

        # Create schedules for the next 30 days
        routes = Route.objects.all()
        today = timezone.now().date()
        
        for route in routes:
            for day in range(30):
                departure_date = today + timedelta(days=day)
                # Skip if schedule already exists
                if Schedule.objects.filter(route=route, departure_date=departure_date).exists():
                    continue
                    
                schedule = Schedule.objects.create(
                    route=route,
                    departure_date=departure_date,
                    arrival_date=departure_date,  # Same day arrival
                    total_seats=180,
                    available_seats=180,
                    price=route.base_price,
                    is_active=True,
                    notes=f"Scheduled flight on {departure_date.strftime('%Y-%m-%d')}"
                )
                self.stdout.write(self.style.SUCCESS(f'Created schedule: {schedule}'))

        self.stdout.write(self.style.SUCCESS('Successfully created sample routes and schedules!'))
