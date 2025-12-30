import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Travel_agency.settings')
django.setup()

from travels.models import Flight
from datetime import date, time

# Delete existing Delhi-Dubai flights for 1 Jan 2025
Flight.objects.filter(origin='Delhi', destination='Dubai', departure_date=date(2025, 1, 1)).delete()
print("Deleted existing flights")

# Add 5 different flights for Delhi to Dubai on 1 Jan 2025
flights = [
    Flight(
        origin='Delhi',
        destination='Dubai',
        departure_date=date(2025, 1, 1),
        airline='Air India',
        flight_number='AI191',
        departure_time=time(6, 0),
        arrival_time=time(8, 30),
        price=12500,
        available_seats=45
    ),
    Flight(
        origin='Delhi',
        destination='Dubai',
        departure_date=date(2025, 1, 1),
        airline='IndiGo',
        flight_number='6E1406',
        departure_time=time(10, 30),
        arrival_time=time(13, 0),
        price=11800,
        available_seats=52
    ),
    Flight(
        origin='Delhi',
        destination='Dubai',
        departure_date=date(2025, 1, 1),
        airline='Emirates',
        flight_number='EK512',
        departure_time=time(14, 0),
        arrival_time=time(16, 30),
        price=15200,
        available_seats=38
    ),
    Flight(
        origin='Delhi',
        destination='Dubai',
        departure_date=date(2025, 1, 1),
        airline='SpiceJet',
        flight_number='SG23',
        departure_time=time(18, 30),
        arrival_time=time(21, 0),
        price=10900,
        available_seats=60
    ),
    Flight(
        origin='Delhi',
        destination='Dubai',
        departure_date=date(2025, 1, 1),
        airline='Vistara',
        flight_number='UK109',
        departure_time=time(22, 0),
        arrival_time=time(0, 30),
        price=13400,
        available_seats=42
    )
]

Flight.objects.bulk_create(flights)
print(f"✅ Successfully added {len(flights)} flights for Delhi to Dubai on 1 Jan 2025")

# Verify
final_count = Flight.objects.filter(origin='Delhi', destination='Dubai', departure_date=date(2025, 1, 1)).count()
print(f"✅ Total flights now: {final_count}")

# Show all flights
print("\n📋 Flight Details:")
for flight in Flight.objects.filter(origin='Delhi', destination='Dubai', departure_date=date(2025, 1, 1)).order_by('departure_time'):
    print(f"  {flight.airline} {flight.flight_number} | {flight.departure_time} - {flight.arrival_time} | ₹{flight.price}")
