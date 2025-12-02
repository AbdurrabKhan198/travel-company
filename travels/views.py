from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, date, timedelta
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.conf import settings
from decimal import Decimal
from .models import Schedule, Route, Booking, Package, UserProfile, BookingPassenger, OTPVerification, Contact, ODWallet, ODWalletTransaction, CashBalanceWallet, CashBalanceTransaction, GroupRequest, PackageApplication, Executive, PackageApplication
from .forms import UserRegisterForm, UserLoginForm, ProfileUpdateForm, ContactForm, WalletRechargeForm
import random
import string
import json
import razorpay
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# Comprehensive Airport Codes Dictionary
def get_airport_codes():
    """Returns a comprehensive dictionary of airport codes for major cities worldwide"""
    return {
        # India - Major Cities
        'Mumbai': 'BOM',
        'Delhi': 'DEL',
        'Bangalore': 'BLR',
        'Chennai': 'MAA',
        'Kolkata': 'CCU',
        'Hyderabad': 'HYD',
        'Pune': 'PNQ',
        'Ahmedabad': 'AMD',
        'Goa': 'GOI',
        'Kochi': 'COK',
        'Thiruvananthapuram': 'TRV',
        'Jaipur': 'JAI',
        'Lucknow': 'LKO',
        'Nagpur': 'NAG',
        'Srinagar': 'SXR',
        'Guwahati': 'GAU',
        'Varanasi': 'VNS',
        'Amritsar': 'ATQ',
        'Indore': 'IDR',
        'Bhopal': 'BHO',
        'Chandigarh': 'IXC',
        'Coimbatore': 'CJB',
        'Madurai': 'IXM',
        'Tiruchirappalli': 'TRZ',
        'Visakhapatnam': 'VTZ',
        'Bhubaneswar': 'BBI',
        'Patna': 'PAT',
        'Raipur': 'RPR',
        'Surat': 'STV',
        'Vadodara': 'BDQ',
        'Udaipur': 'UDR',
        'Jodhpur': 'JDH',
        'Dehradun': 'DED',
        'Shimla': 'SLV',
        
        # Middle East - UAE
        'Dubai': 'DXB',
        'Abu Dhabi': 'AUH',
        'Sharjah': 'SHJ',
        'Al Ain': 'AAN',
        'Ras Al Khaimah': 'RKT',
        
        # Middle East - Saudi Arabia
        'Riyadh': 'RUH',
        'Jeddah': 'JED',
        'Dammam': 'DMM',
        'Medina': 'MED',
        'Abha': 'AHB',
        'Tabuk': 'TUU',
        'Taif': 'TIF',
        'Hail': 'HAS',
        'Qassim': 'ELQ',
        
        # Middle East - Qatar
        'Doha': 'DOH',
        
        # Middle East - Kuwait
        'Kuwait': 'KWI',
        'Kuwait City': 'KWI',
        
        # Middle East - Bahrain
        'Bahrain': 'BAH',
        'Manama': 'BAH',
        
        # Middle East - Oman
        'Muscat': 'MCT',
        'Salalah': 'SLL',
        
        # Middle East - Jordan
        'Amman': 'AMM',
        
        # Middle East - Lebanon
        'Beirut': 'BEY',
        
        # Middle East - Israel
        'Tel Aviv': 'TLV',
        'Jerusalem': 'JRS',
        
        # Middle East - Egypt
        'Cairo': 'CAI',
        'Alexandria': 'ALY',
        'Sharm El Sheikh': 'SSH',
        'Hurghada': 'HRG',
        
        # Middle East - Turkey
        'Istanbul': 'IST',
        'Ankara': 'ESB',
        'Antalya': 'AYT',
        
        # Middle East - Iran
        'Tehran': 'IKA',
        'Shiraz': 'SYZ',
        'Isfahan': 'IFN',
        
        # Asia - Southeast
        'Singapore': 'SIN',
        'Bangkok': 'BKK',
        'Phuket': 'HKT',
        'Kuala Lumpur': 'KUL',
        'Penang': 'PEN',
        'Jakarta': 'CGK',
        'Bali': 'DPS',
        'Manila': 'MNL',
        'Cebu': 'CEB',
        'Ho Chi Minh': 'SGN',
        'Hanoi': 'HAN',
        'Phnom Penh': 'PNH',
        'Yangon': 'RGN',
        'Vientiane': 'VTE',
        
        # Asia - East
        'Hong Kong': 'HKG',
        'Macau': 'MFM',
        'Shanghai': 'PVG',
        'Beijing': 'PEK',
        'Guangzhou': 'CAN',
        'Shenzhen': 'SZX',
        'Chengdu': 'CTU',
        'Xi\'an': 'XIY',
        'Tokyo': 'NRT',
        'Osaka': 'KIX',
        'Seoul': 'ICN',
        'Busan': 'PUS',
        'Taipei': 'TPE',
        'Kaohsiung': 'KHH',
        
        # Asia - South
        'Colombo': 'CMB',
        'Male': 'MLE',
        'Kathmandu': 'KTM',
        'Dhaka': 'DAC',
        'Karachi': 'KHI',
        'Lahore': 'LHE',
        'Islamabad': 'ISB',
        'Rawalpindi': 'RWP',
        
        # Europe - UK & Ireland
        'London': 'LHR',
        'Manchester': 'MAN',
        'Edinburgh': 'EDI',
        'Birmingham': 'BHX',
        'Glasgow': 'GLA',
        'Dublin': 'DUB',
        'Cork': 'ORK',
        
        # Europe - Western
        'Paris': 'CDG',
        'Lyon': 'LYS',
        'Nice': 'NCE',
        'Marseille': 'MRS',
        'Frankfurt': 'FRA',
        'Munich': 'MUC',
        'Berlin': 'BER',
        'Hamburg': 'HAM',
        'Amsterdam': 'AMS',
        'Brussels': 'BRU',
        'Zurich': 'ZRH',
        'Geneva': 'GVA',
        'Vienna': 'VIE',
        'Madrid': 'MAD',
        'Barcelona': 'BCN',
        'Lisbon': 'LIS',
        'Porto': 'OPO',
        'Rome': 'FCO',
        'Milan': 'MXP',
        'Venice': 'VCE',
        'Naples': 'NAP',
        
        # Europe - Northern
        'Copenhagen': 'CPH',
        'Stockholm': 'ARN',
        'Oslo': 'OSL',
        'Helsinki': 'HEL',
        'Reykjavik': 'KEF',
        
        # Europe - Eastern
        'Warsaw': 'WAW',
        'Prague': 'PRG',
        'Budapest': 'BUD',
        'Bucharest': 'OTP',
        'Sofia': 'SOF',
        'Athens': 'ATH',
        'Belgrade': 'BEG',
        'Zagreb': 'ZAG',
        
        # North America - USA
        'New York': 'JFK',
        'Los Angeles': 'LAX',
        'Chicago': 'ORD',
        'San Francisco': 'SFO',
        'Miami': 'MIA',
        'Boston': 'BOS',
        'Washington': 'IAD',
        'Seattle': 'SEA',
        'Atlanta': 'ATL',
        'Dallas': 'DFW',
        'Houston': 'IAH',
        'Las Vegas': 'LAS',
        'Phoenix': 'PHX',
        'Denver': 'DEN',
        'Philadelphia': 'PHL',
        'Detroit': 'DTW',
        'Minneapolis': 'MSP',
        'Orlando': 'MCO',
        
        # North America - Canada
        'Toronto': 'YYZ',
        'Vancouver': 'YVR',
        'Montreal': 'YUL',
        'Calgary': 'YYC',
        'Ottawa': 'YOW',
        'Edmonton': 'YEG',
        
        # North America - Mexico
        'Mexico City': 'MEX',
        'Cancun': 'CUN',
        'Guadalajara': 'GDL',
        
        # South America
        'São Paulo': 'GRU',
        'Rio de Janeiro': 'GIG',
        'Buenos Aires': 'EZE',
        'Lima': 'LIM',
        'Bogotá': 'BOG',
        'Santiago': 'SCL',
        'Caracas': 'CCS',
        
        # Africa
        'Johannesburg': 'JNB',
        'Cape Town': 'CPT',
        'Cairo': 'CAI',
        'Casablanca': 'CMN',
        'Lagos': 'LOS',
        'Nairobi': 'NBO',
        'Addis Ababa': 'ADD',
        'Accra': 'ACC',
        
        # Australia & Oceania
        'Sydney': 'SYD',
        'Melbourne': 'MEL',
        'Brisbane': 'BNE',
        'Perth': 'PER',
        'Adelaide': 'ADL',
        'Auckland': 'AKL',
        'Wellington': 'WLG',
        'Christchurch': 'CHC',
        'Fiji': 'NAN',
        'Honolulu': 'HNL',
    }


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def homepage(request):
    """Homepage with search and featured packages"""
    packages = Package.objects.filter(is_featured=True)[:6]
    
    # Define popular package destinations with Unsplash images
    popular_packages = [
        {
            'name': 'Thailand', 
            'destination': 'Thailand', 
            'icon': '🇹🇭',
            'image': 'https://images.unsplash.com/photo-1552465011-b4e21bf6e79a?w=800&h=600&fit=crop',
            'description': 'Experience the vibrant culture, stunning beaches, and delicious cuisine of Thailand'
        },
        {
            'name': 'Dubai', 
            'destination': 'Dubai', 
            'icon': '🇦🇪',
            'image': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800&h=600&fit=crop',
            'description': 'Discover luxury, modern architecture, and desert adventures in Dubai'
        },
        {
            'name': 'Singapore', 
            'destination': 'Singapore', 
            'icon': '🇸🇬',
            'image': 'https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=800&h=600&fit=crop',
            'description': 'Explore the perfect blend of culture, cuisine, and cutting-edge innovation'
        },
        {
            'name': 'Bali', 
            'destination': 'Bali', 
            'icon': '🇮🇩',
            'image': 'https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?w=800&h=600&fit=crop',
            'description': 'Relax on pristine beaches and immerse in Balinese culture and spirituality'
        },
        {
            'name': 'Vietnam', 
            'destination': 'Vietnam', 
            'icon': '🇻🇳',
            'image': 'https://images.unsplash.com/photo-1528127269322-539801943592?w=800&h=600&fit=crop',
            'description': 'Journey through rich history, breathtaking landscapes, and amazing food'
        },
    ]
    
    # Get airport codes dictionary
    airport_codes = get_airport_codes()
    
    # Get unique locations from database routes
    origins_list = list(Route.objects.values_list('from_location', flat=True).distinct())
    destinations_list = list(Route.objects.values_list('to_location', flat=True).distinct())
    
    # Combine database locations with all cities from airport_codes
    # This ensures all cities (including Lucknow) appear in dropdown even if no routes exist yet
    all_cities = set(airport_codes.keys())
    origins_set = set(origins_list) | all_cities
    destinations_set = set(destinations_list) | all_cities
    
    origins = sorted(list(origins_set))
    destinations = sorted(list(destinations_set))
    
    # Get available dates from Schedule (admin-controlled dates only)
    available_dates = Schedule.objects.filter(
        is_active=True,
        departure_date__gte=date.today(),
        available_seats__gt=0
    ).values_list('departure_date', flat=True).distinct().order_by('departure_date')
    
    # Convert to list of date strings for JavaScript
    available_dates_list = [d.isoformat() for d in available_dates]
    
    # Get active executives for header
    executives = Executive.objects.filter(is_active=True).order_by('display_order', 'name')
    
    context = {
        'packages': packages,
        'popular_packages': popular_packages,
        'origins': origins,
        'destinations': destinations,
        'today': date.today().isoformat(),
        'available_dates': available_dates_list,
        'airport_codes': airport_codes,
        'executives': executives,
    }
    return render(request, 'index.html', context)


def search_flights(request):
    """Search for available flights with enhanced functionality"""
    from_location = request.GET.get('from_location', '').strip()
    to_location = request.GET.get('to_location', '').strip()
    travel_date = request.GET.get('travel_date', '').strip()
    return_date = request.GET.get('return_date', '').strip()
    route_type = request.GET.get('route_type', '').strip()
    trip_type = request.GET.get('trip_type', 'one_way').strip()
    
    # Get passenger counts (adults, children, infants)
    try:
        adults = int(request.GET.get('adults', 1))
        children = int(request.GET.get('children', 0))
        infants = int(request.GET.get('infants', 0))
    except (ValueError, TypeError):
        adults = 1
        children = 0
        infants = 0
    
    # Validate at least 1 adult
    if adults < 1:
        adults = 1
    
    # Validate infants don't exceed adults
    if infants > adults:
        messages.error(request, 'Number of infants cannot exceed number of adults.')
        return redirect('homepage')
    
    # Calculate total passengers for seat availability check
    passengers = adults + children  # Infants don't need seats
    
    # Get comprehensive airport codes
    airport_codes = get_airport_codes()
    
    # Extract city name from input (remove airport codes in parentheses)
    import re
    def extract_city_name(location_str):
        if not location_str:
            return ''
        # Remove airport code in parentheses like "Delhi (DEL)" -> "Delhi"
        match = re.match(r'^(.+?)(\s*\([^)]+\))?$', location_str.strip())
        if match:
            return match.group(1).strip()
        return location_str.strip()
    
    from_location = extract_city_name(from_location)
    to_location = extract_city_name(to_location)
    
    # Validate required fields
    if not from_location or not to_location:
        messages.error(request, 'Please select both origin and destination.')
        return redirect('homepage')
    
    if from_location == to_location:
        messages.error(request, 'Origin and destination cannot be the same.')
        return redirect('homepage')
    
    # Start with base query - use case-insensitive matching
    base_flights = Schedule.objects.select_related('route').filter(
        route__from_location__iexact=from_location,
        route__to_location__iexact=to_location,
        is_active=True
    )
    
    # First try with route type filter if specified
    flights = base_flights
    if route_type and route_type in dict(Route.ROUTE_TYPE_CHOICES):
        flights = base_flights.filter(route__route_type=route_type)
        # If no flights found with route type, try without route type filter
        if not flights.exists():
            flights = base_flights
            messages.info(request, f'No {route_type} flights found. Showing all available flights.')
    
    # Filter by travel date if specified
    if travel_date:
        try:
            travel_date_obj = datetime.strptime(travel_date, '%Y-%m-%d').date()
            if travel_date_obj < timezone.now().date():
                messages.error(request, 'Please select a future date.')
                return redirect('homepage')
            flights = flights.filter(departure_date=travel_date_obj)
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('homepage')
    
    # Filter only future dates
    flights = flights.filter(departure_date__gte=timezone.now().date())
    
    # Filter flights with enough available seats
    flights = flights.filter(available_seats__gte=passengers)
    
    # Order by price and departure date
    flights = flights.order_by('price', 'departure_date')
    
    # Search for return flights if trip_type is 'return'
    return_flights = None
    if trip_type == 'return' and return_date:
        try:
            return_date_obj = datetime.strptime(return_date, '%Y-%m-%d').date()
            if return_date_obj < timezone.now().date():
                messages.error(request, 'Return date must be in the future.')
                return redirect('homepage')
            
            # Validate return date is after departure date
            if travel_date:
                travel_date_obj = datetime.strptime(travel_date, '%Y-%m-%d').date()
                if return_date_obj <= travel_date_obj:
                    messages.error(request, 'Return date must be after departure date.')
                    return redirect('homepage')
            
            # Search for return flights (reverse route: to_location -> from_location)
            return_base_flights = Schedule.objects.select_related('route').filter(
                route__from_location__iexact=to_location,
                route__to_location__iexact=from_location,
                is_active=True
            )
            
            # Apply route type filter if specified
            if route_type and route_type in dict(Route.ROUTE_TYPE_CHOICES):
                return_base_flights = return_base_flights.filter(route__route_type=route_type)
            
            # Filter by return date
            return_flights = return_base_flights.filter(departure_date=return_date_obj)
            
            # Filter only future dates
            return_flights = return_flights.filter(departure_date__gte=timezone.now().date())
            
            # Filter flights with enough available seats
            return_flights = return_flights.filter(available_seats__gte=passengers)
            
            # Order by price and departure date
            return_flights = return_flights.order_by('price', 'departure_date')
            
        except ValueError:
            messages.error(request, 'Invalid return date format.')
            return redirect('homepage')
    
    # Get route information
    route_info = None
    if flights.exists():
        route_info = flights.first().route
    
    # Get airport codes for display
    from_airport_code = airport_codes.get(from_location, '')
    to_airport_code = airport_codes.get(to_location, '')
    
    # Get travel class if provided
    travel_class = request.GET.get('travel_class', 'economy').strip()
    
    context = {
        'flights': flights,
        'return_flights': return_flights,
        'from_location': from_location,
        'to_location': to_location,
        'from_airport_code': from_airport_code,
        'to_airport_code': to_airport_code,
        'airport_codes': airport_codes,  # Pass the full dictionary for individual flights
        'travel_date': travel_date,
        'return_date': return_date,
        'trip_type': trip_type,
        'route_type': route_type,
        'passengers': passengers,  # Total passengers (adults + children) for seat availability
        'adults': adults,
        'children': children,
        'infants': infants,
        'travel_class': travel_class,
        'route_info': route_info,
        'total_flights': flights.count(),
        'total_return_flights': return_flights.count() if return_flights else 0,
    }
    return render(request, 'search.html', context)


@login_required
def booking_page(request, schedule_id):
    """B2B Booking page for a specific flight with multiple passenger support"""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # Get passenger counts (adults, children, infants)
    try:
        adults = int(request.GET.get('adults', request.GET.get('passengers', 1)))
        children = int(request.GET.get('children', 0))
        infants = int(request.GET.get('infants', 0))
    except (ValueError, TypeError):
        adults = 1
        children = 0
        infants = 0
    
    # Validate at least 1 adult
    if adults < 1:
        adults = 1
    
    # Validate infants don't exceed adults
    if infants > adults:
        messages.error(request, 'Number of infants cannot exceed number of adults.')
        return redirect('search_flights')
    
    # Calculate total passengers for seat availability (infants don't need seats)
    passengers = adults + children
    
    return_schedule_id = request.GET.get('return_schedule_id', None)
    trip_type = request.GET.get('trip_type', 'one_way')
    travel_class = request.GET.get('travel_class', 'economy')
    
    # Get return schedule if provided
    return_schedule = None
    if return_schedule_id and trip_type == 'return':
        try:
            return_schedule = Schedule.objects.get(id=return_schedule_id)
        except Schedule.DoesNotExist:
            messages.error(request, 'Return flight not found.')
            return redirect('search_flights')
    
    # Ensure passengers doesn't exceed available seats
    if passengers > schedule.available_seats:
        passengers = schedule.available_seats
        messages.warning(request, f'Maximum {passengers} passengers can be booked for this flight.')
    
    if request.method == 'POST':
        # Check if this is a review confirmation (from review page)
        if request.POST.get('action') == 'confirm_booking':
            return handle_booking_confirmation(request, schedule_id)
        
        # Process booking form submission - redirect to review
        # seats_booked = adults + children (infants don't need seats)
        seats_booked = adults + children
        
        # Check availability
        if schedule.available_seats < seats_booked:
            messages.error(request, f'Not enough seats available! Only {schedule.available_seats} seats left.')
            # Preserve passenger counts in redirect
            from urllib.parse import urlencode
            redirect_params = {
                'adults': adults,
                'children': children,
                'infants': infants,
            }
            if return_schedule_id:
                redirect_params['return_schedule_id'] = return_schedule_id
            if trip_type:
                redirect_params['trip_type'] = trip_type
            if travel_class:
                redirect_params['travel_class'] = travel_class
            redirect_url = f"{reverse('booking', args=[schedule_id])}?{urlencode(redirect_params)}"
            return redirect(redirect_url)
        
        # Get passenger details
        passenger_titles = request.POST.getlist('passenger_title[]')
        passenger_first_names = request.POST.getlist('passenger_first_name[]')
        passenger_last_names = request.POST.getlist('passenger_last_name[]')
        passenger_dobs = request.POST.getlist('passenger_dob[]')
        passenger_genders = request.POST.getlist('passenger_gender[]')
        passenger_types = request.POST.getlist('passenger_type[]')
        passport_numbers = request.POST.getlist('passport_number[]')
        passport_expiries = request.POST.getlist('passport_expiry[]')
        nationalities = request.POST.getlist('nationality[]')
        contact_email = request.POST.get('contact_email', request.user.email)
        contact_phone = request.POST.get('contact_phone', '')
        
        # Validate passenger details - check all required fields
        validation_errors = []
        
        # Check if we have the right number of passenger forms
        expected_passengers = adults + children + infants
        if len(passenger_first_names) != expected_passengers:
            validation_errors.append(f'Expected {expected_passengers} passengers but got {len(passenger_first_names)} forms.')
        
        # Validate each passenger's required fields
        max_index = max(len(passenger_first_names), len(passenger_last_names), len(passenger_dobs), 
                       len(passenger_genders), len(passenger_titles), len(nationalities))
        
        for i in range(expected_passengers):
            if i >= len(passenger_first_names) or not passenger_first_names[i] or not passenger_first_names[i].strip():
                validation_errors.append(f'Passenger {i+1}: First name is required.')
            if i >= len(passenger_last_names) or not passenger_last_names[i] or not passenger_last_names[i].strip():
                validation_errors.append(f'Passenger {i+1}: Last name is required.')
            if i >= len(passenger_dobs) or not passenger_dobs[i] or not passenger_dobs[i].strip():
                validation_errors.append(f'Passenger {i+1}: Date of birth is required.')
            if i >= len(passenger_genders) or not passenger_genders[i] or not passenger_genders[i].strip():
                validation_errors.append(f'Passenger {i+1}: Gender is required.')
            if i >= len(passenger_titles) or not passenger_titles[i] or not passenger_titles[i].strip():
                validation_errors.append(f'Passenger {i+1}: Title is required.')
            if i >= len(nationalities) or not nationalities[i] or not nationalities[i].strip():
                validation_errors.append(f'Passenger {i+1}: Nationality is required.')
        
        # Validate contact information
        if not contact_email or not contact_email.strip():
            validation_errors.append('Contact email is required.')
        if not contact_phone or not contact_phone.strip():
            validation_errors.append('Contact phone is required.')
        
        if validation_errors:
            error_msg = 'Please fill in all required fields. ' + ' '.join(validation_errors[:3])
            if len(validation_errors) > 3:
                error_msg += f' (and {len(validation_errors) - 3} more)'
            messages.error(request, error_msg)
            # Preserve adults/children/infants counts in redirect
            from urllib.parse import urlencode
            redirect_params = {
                'adults': adults,
                'children': children,
                'infants': infants,
            }
            if return_schedule_id:
                redirect_params['return_schedule_id'] = return_schedule_id
            if trip_type:
                redirect_params['trip_type'] = trip_type
            if travel_class:
                redirect_params['travel_class'] = travel_class
            redirect_url = f"{reverse('booking', args=[schedule_id])}?{urlencode(redirect_params)}"
            return redirect(redirect_url)
        
        # Store passenger data in session for review page
        # Include ALL passengers: adults + children + infants
        total_passengers = adults + children + infants
        passenger_data = []
        for i in range(total_passengers):
            passenger_data.append({
                'title': passenger_titles[i] if i < len(passenger_titles) else 'Mr',
                'first_name': passenger_first_names[i],
                'last_name': passenger_last_names[i],
                'dob': passenger_dobs[i],
                'gender': passenger_genders[i],
                'passenger_type': passenger_types[i] if i < len(passenger_types) else 'adult',
                'passport_number': passport_numbers[i] if i < len(passport_numbers) else '',
                'passport_expiry': passport_expiries[i] if i < len(passport_expiries) else '',
                'nationality': nationalities[i] if i < len(nationalities) else 'Indian',
            })
        
        # Get return schedule if provided
        return_schedule_id = request.POST.get('return_schedule_id', return_schedule_id)
        return_schedule = None
        if return_schedule_id and trip_type == 'return':
            try:
                return_schedule = Schedule.objects.get(id=return_schedule_id)
                # Check return flight availability
                if return_schedule.available_seats < seats_booked:
                    messages.error(request, f'Not enough seats available on return flight! Only {return_schedule.available_seats} seats left.')
                    return redirect('booking', schedule_id=schedule_id)
            except Schedule.DoesNotExist:
                messages.error(request, 'Return flight not found.')
                return redirect('booking', schedule_id=schedule_id)
        
        # Calculate amounts (different prices for adult/child/infant)
        base_fare = Decimal('0')
        adult_count = sum(1 for p in passenger_data if p['passenger_type'] == 'adult')
        child_count = sum(1 for p in passenger_data if p['passenger_type'] == 'child')
        infant_count = sum(1 for p in passenger_data if p['passenger_type'] == 'infant')
        
        # Pricing: Use specific fares from Schedule model, fallback to calculated prices if not set
        adult_price = schedule.get_fare_for_passenger_type('adult')
        child_price = schedule.get_fare_for_passenger_type('child')
        infant_price = schedule.get_fare_for_passenger_type('infant')
        
        # Outbound flight fare
        outbound_fare = (adult_price * adult_count) + (child_price * child_count) + (infant_price * infant_count)
        
        # Return flight fare (if return trip)
        return_fare = Decimal('0')
        if return_schedule:
            return_adult_price = return_schedule.get_fare_for_passenger_type('adult')
            return_child_price = return_schedule.get_fare_for_passenger_type('child')
            return_infant_price = return_schedule.get_fare_for_passenger_type('infant')
            return_fare = (return_adult_price * adult_count) + (return_child_price * child_count) + (return_infant_price * infant_count)
        
        base_fare = outbound_fare + return_fare
        tax_amount = base_fare * Decimal('0.18')  # 18% GST
        total_amount = base_fare + tax_amount
        
        # Store in session for review
        request.session['booking_data'] = {
            'schedule_id': schedule_id,
            'return_schedule_id': return_schedule_id if return_schedule else None,
            'trip_type': trip_type,
            'seats_booked': seats_booked,  # For seat availability (adults + children only)
            'total_passengers': total_passengers,  # Total including infants
            'passenger_data': passenger_data,
            'contact_email': contact_email,
            'contact_phone': contact_phone,
            'base_fare': str(base_fare),
            'tax_amount': str(tax_amount),
            'total_amount': str(total_amount),
            'adult_count': adult_count,
            'child_count': child_count,
            'infant_count': infant_count,
            'outbound_fare': str(outbound_fare),
            'return_fare': str(return_fare) if return_schedule else '0',
            'adult_fare_per_passenger': str(adult_price),
            'child_fare_per_passenger': str(child_price),
            'infant_fare_per_passenger': str(infant_price),
            'return_adult_fare_per_passenger': str(return_adult_price) if return_schedule else '0',
            'return_child_fare_per_passenger': str(return_child_price) if return_schedule else '0',
            'return_infant_fare_per_passenger': str(return_infant_price) if return_schedule else '0',
        }
        
        # Redirect to review page
        return redirect('review_booking', schedule_id=schedule_id)
    
    # Get return schedule if provided
    return_schedule = None
    if return_schedule_id and trip_type == 'return':
        try:
            return_schedule = Schedule.objects.get(id=return_schedule_id)
        except Schedule.DoesNotExist:
            pass
    
    # Get comprehensive airport codes
    airport_codes = get_airport_codes()
    
    # Get fare information
    adult_fare = schedule.get_fare_for_passenger_type('adult')
    child_fare = schedule.get_fare_for_passenger_type('child')
    infant_fare = schedule.get_fare_for_passenger_type('infant')
    
    return_adult_fare = None
    return_child_fare = None
    return_infant_fare = None
    if return_schedule:
        return_adult_fare = return_schedule.get_fare_for_passenger_type('adult')
        return_child_fare = return_schedule.get_fare_for_passenger_type('child')
        return_infant_fare = return_schedule.get_fare_for_passenger_type('infant')
    
    # Create separate ranges for each passenger type
    adult_range = range(1, adults + 1) if adults > 0 else []
    child_range = range(1, children + 1) if children > 0 else []
    infant_range = range(1, infants + 1) if infants > 0 else []
    
    context = {
        'schedule': schedule,
        'return_schedule': return_schedule,
        'trip_type': trip_type,
        'passengers': passengers,  # Total for seat availability
        'adults': adults,
        'children': children,
        'infants': infants,
        'travel_class': travel_class,
        'passenger_range': range(1, passengers + 1),
        'adult_range': adult_range,
        'child_range': child_range,
        'infant_range': infant_range,
        'airport_codes': airport_codes,
        'today': date.today().isoformat(),
        'user': request.user,
        'adult_fare': adult_fare,
        'child_fare': child_fare,
        'infant_fare': infant_fare,
        'return_adult_fare': return_adult_fare,
        'return_child_fare': return_child_fare,
        'return_infant_fare': return_infant_fare,
    }
    return render(request, 'booking.html', context)

@login_required
def review_booking(request, schedule_id):
    """Review booking details before confirmation"""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # Get booking data from session
    booking_data = request.session.get('booking_data')
    if not booking_data or booking_data.get('schedule_id') != schedule_id:
        messages.error(request, 'Please complete the booking form first.')
        return redirect('booking', schedule_id=schedule_id)
    
    # Get return schedule if it's a return trip
    return_schedule = None
    trip_type = booking_data.get('trip_type', 'one_way')
    return_schedule_id = booking_data.get('return_schedule_id')
    if return_schedule_id and trip_type == 'return':
        try:
            return_schedule = Schedule.objects.get(id=return_schedule_id)
        except Schedule.DoesNotExist:
            pass
    
    # Get comprehensive airport codes
    airport_codes = get_airport_codes()
    
    context = {
        'schedule': schedule,
        'return_schedule': return_schedule,
        'trip_type': trip_type,
        'booking_data': booking_data,
        'airport_codes': airport_codes,
        'passenger_data': booking_data.get('passenger_data', []),
    }
    return render(request, 'review_booking.html', context)

def handle_booking_confirmation(request, schedule_id):
    """Handle final booking confirmation after review"""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    # Get booking data from session
    booking_data = request.session.get('booking_data')
    if not booking_data or booking_data.get('schedule_id') != schedule_id:
        messages.error(request, 'Session expired. Please start booking again.')
        return redirect('booking', schedule_id=schedule_id)
    
    seats_booked = booking_data.get('seats_booked', 1)
    
    # Check availability again
    if schedule.available_seats < seats_booked:
        messages.error(request, f'Not enough seats available! Only {schedule.available_seats} seats left.')
        return redirect('booking', schedule_id=schedule_id)
    
    # Get return schedule if it's a return trip
    return_schedule = None
    trip_type = booking_data.get('trip_type', 'one_way')
    return_schedule_id = booking_data.get('return_schedule_id')
    if return_schedule_id and trip_type == 'return':
        try:
            return_schedule = Schedule.objects.get(id=return_schedule_id)
            # Check return flight availability
            if return_schedule.available_seats < seats_booked:
                messages.error(request, f'Not enough seats available on return flight! Only {return_schedule.available_seats} seats left.')
                return redirect('booking', schedule_id=schedule_id)
        except Schedule.DoesNotExist:
            messages.error(request, 'Return flight not found.')
            return redirect('booking', schedule_id=schedule_id)
    
    # Create booking (PENDING status until payment)
    booking = Booking.objects.create(
        user=request.user,
        schedule=schedule,
        return_schedule=return_schedule,
        trip_type=trip_type,
        contact_email=booking_data.get('contact_email', request.user.email),
        contact_phone=booking_data.get('contact_phone', ''),
        base_fare=Decimal(booking_data.get('base_fare', '0')),
        tax_amount=Decimal(booking_data.get('tax_amount', '0')),
        total_amount=Decimal(booking_data.get('total_amount', '0')),
        status=Booking.Status.PENDING,
        payment_status=Booking.PaymentStatus.PENDING,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Create BookingPassenger records
    from datetime import datetime
    passenger_data = booking_data.get('passenger_data', [])
    for passenger in passenger_data:
        dob = datetime.strptime(passenger['dob'], '%Y-%m-%d').date() if passenger.get('dob') else None
        passport_expiry = datetime.strptime(passenger['passport_expiry'], '%Y-%m-%d').date() if passenger.get('passport_expiry') and passenger['passport_expiry'] else None
        
        BookingPassenger.objects.create(
            booking=booking,
            title=passenger.get('title', 'Mr'),
            first_name=passenger['first_name'],
            last_name=passenger['last_name'],
            date_of_birth=dob,
            gender=passenger['gender'],
            passenger_type=passenger.get('passenger_type', 'adult'),
            passport_number=passenger.get('passport_number', ''),
            passport_expiry=passport_expiry,
            nationality=passenger.get('nationality', 'Indian')
        )
    
    # Clear session data
    if 'booking_data' in request.session:
        del request.session['booking_data']
    
    # Redirect to payment page
    return redirect('payment', booking_id=booking.id)

def contact(request):
    """Handle contact form submission"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save contact inquiry to database
            contact = Contact.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data.get('phone', ''),
                subject=form.cleaned_data.get('subject', ''),
                message=form.cleaned_data['message'],
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            
            # Redirect to thanks page
            return redirect('contact_thanks', contact_id=contact.id)
        else:
            # Form has errors, show them
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {'form': form})


def contact_thanks(request, contact_id):
    """Thank you page after contact form submission"""
    try:
        contact = Contact.objects.get(id=contact_id)
    except Contact.DoesNotExist:
        messages.error(request, 'Contact inquiry not found.')
        return redirect('contact')
    
    return render(request, 'thanks.html', {'contact': contact})

def visit_visa(request):
    """Visit Visa services page"""
    return render(request, 'visit_visa.html')

def apply_visa(request):
    """Visa application form"""
    country = request.GET.get('country', '')
    duration = request.GET.get('duration', '')
    price = request.GET.get('price', '')
    
    # Visa data mapping
    visa_data = {
        'qatar': {'name': 'Qatar', 'flag': '🇶🇦', 'durations': [{'days': 30, 'price': 500, 'entry': 'Single Entry'}]},
        'bahrain': {'name': 'Bahrain', 'flag': '🇧🇭', 'durations': [{'days': 30, 'price': 4900}, {'days': 14, 'price': 3000}, {'days': 90, 'price': 11300}]},
        'oman': {'name': 'Oman', 'flag': '🇴🇲', 'durations': [{'days': 30, 'price': 5100}, {'days': 10, 'price': 1700}, {'days': 90, 'price': 22000}], 'note': 'Female charges High'},
        'azerbaijan': {'name': 'Azerbaijan', 'flag': '🇦🇿', 'durations': [{'days': 30, 'price': 3000}]},
        'uzbekistan': {'name': 'Uzbekistan', 'flag': '🇺🇿', 'durations': [{'days': 30, 'price': 3100}]},
        'vietnam': {'name': 'Vietnam', 'flag': '🇻🇳', 'durations': [{'days': 30, 'price': 3000, 'entry': 'Single Entry'}]},
        'cambodia': {'name': 'Cambodia', 'flag': '🇰🇭', 'durations': [{'days': 30, 'price': 3200}]},
        'russia': {'name': 'Russia', 'flag': '🇷🇺', 'durations': [{'days': 30, 'price': 5800}]},
        'dubai': {'name': 'Dubai', 'flag': '🇦🇪', 'durations': [{'days': 30, 'price': 10700}, {'days': 60, 'price': 14500}]},
    }
    
    selected_visa = visa_data.get(country.lower(), {})
    
    if request.method == 'POST':
        # Handle form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        selected_duration = request.POST.get('duration')
        selected_price = request.POST.get('price')
        travel_date = request.POST.get('travel_date')
        passport_number = request.POST.get('passport_number')
        passport_expiry = request.POST.get('passport_expiry')
        address = request.POST.get('address')
        notes = request.POST.get('notes', '')
        
        # Here you would save to database or send email
        # For now, we'll just show a success message
        messages.success(request, f'Your visa application for {selected_visa.get("name", country)} has been submitted successfully! We will contact you soon.')
        return redirect('visit_visa')
    
    context = {
        'country': country,
        'duration': duration,
        'price': price,
        'visa': selected_visa,
    }
    return render(request, 'apply_visa.html', context)

def about(request):
    return render(request, 'about.html')

def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'privacy_policy.html')

def terms_conditions(request):
    """Terms and Conditions page"""
    return render(request, 'terms_conditions.html')

def faq(request):
    """FAQ page"""
    return render(request, 'faq.html')

@login_required
def dashboard(request):
    """User dashboard with bookings"""
    # Handle logo upload
    if request.method == 'POST' and 'logo' in request.FILES:
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'full_name': request.user.get_full_name() or request.user.email.split('@')[0]}
        )
        profile.logo = request.FILES['logo']
        profile.save()
        messages.success(request, 'Logo uploaded successfully!')
        return redirect('dashboard')
    
    # Ensure user has a profile (auto-create if missing)
    profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'full_name': request.user.get_full_name() or request.user.email.split('@')[0]}
    )
    
    # Fix any profiles with invalid full_name (like "NONE None" or empty)
    if not profile.full_name or profile.full_name.strip() == '' or profile.full_name.lower() in ['none none', 'none']:
        profile.full_name = request.user.get_full_name() or request.user.email.split('@')[0] or request.user.username
        profile.save()
    
    today = timezone.now().date()
    
    # Get all bookings
    all_bookings = Booking.objects.filter(user=request.user).select_related('schedule__route')
    
    upcoming_bookings = all_bookings.filter(
        schedule__departure_date__gte=today,
        status=Booking.Status.CONFIRMED
    )
    
    past_bookings = all_bookings.filter(
        schedule__departure_date__lt=today,
        status=Booking.Status.CONFIRMED
    )
    
    cancelled_bookings = all_bookings.filter(status=Booking.Status.CANCELLED)
    
    # Calculate total spent
    total_spent = all_bookings.filter(
        payment_status=Booking.PaymentStatus.PAID
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0')
    
    # Get OD Wallet information (admin controlled)
    od_wallet = None
    od_wallet_balance = Decimal('0')
    has_od_wallet_access = False
    try:
        od_wallet = ODWallet.objects.get(user=request.user)
        od_wallet_balance = od_wallet.balance
        has_od_wallet_access = od_wallet.is_active
    except ODWallet.DoesNotExist:
        pass
    
    # Get Cash Balance Wallet information (user self-recharge, direct access)
    cash_balance_wallet = None
    cash_balance = Decimal('0')
    try:
        cash_balance_wallet = CashBalanceWallet.objects.get(user=request.user)
        cash_balance = cash_balance_wallet.balance
    except CashBalanceWallet.DoesNotExist:
        # Create cash balance wallet if it doesn't exist (auto-create for all users)
        cash_balance_wallet = CashBalanceWallet.objects.create(user=request.user)
        cash_balance = Decimal('0')
    
    # Get comprehensive airport codes
    airport_codes = get_airport_codes()
    
    context = {
        'total_bookings': all_bookings.count(),
        'upcoming_count': upcoming_bookings.count(),
        'completed_count': past_bookings.count(),
        'total_spent': total_spent,
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'cancelled_bookings': cancelled_bookings,
        'airport_codes': airport_codes,
        'user': request.user,
        'profile': profile,
        'od_wallet': od_wallet,
        'od_wallet_balance': od_wallet_balance,
        'has_od_wallet_access': has_od_wallet_access,
        'cash_balance_wallet': cash_balance_wallet,
        'cash_balance': cash_balance,
    }
    return render(request, 'dashboard_new.html', context)


@login_required
def my_trips(request):
    """My Trips page with date range filtering and Past/Upcoming/Completed tabs"""
    from datetime import datetime, date
    from django.db.models import Q
    
    today = timezone.now().date()
    
    # Get filter parameters
    from_date_str = request.GET.get('from_date', '')
    to_date_str = request.GET.get('to_date', '')
    trip_type_filter = request.GET.get('trip_type', 'all')  # all, upcoming, past, completed
    
    # Parse date filters
    from_date = None
    to_date = None
    if from_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    if to_date_str:
        try:
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Get all bookings for the user
    all_bookings = Booking.objects.filter(user=request.user).select_related(
        'schedule__route', 'return_schedule__route'
    ).prefetch_related('passengers').order_by('-schedule__departure_date', '-created_at')
    
    # Apply date range filter
    if from_date:
        all_bookings = all_bookings.filter(schedule__departure_date__gte=from_date)
    if to_date:
        all_bookings = all_bookings.filter(schedule__departure_date__lte=to_date)
    
    # Categorize bookings
    upcoming_bookings = all_bookings.filter(
        schedule__departure_date__gte=today,
        status=Booking.Status.CONFIRMED
    )
    
    past_bookings = all_bookings.filter(
        schedule__departure_date__lt=today,
        status=Booking.Status.CONFIRMED
    )
    
    completed_bookings = all_bookings.filter(
        status=Booking.Status.COMPLETED
    )
    
    cancelled_bookings = all_bookings.filter(
        status=Booking.Status.CANCELLED
    )
    
    # Get airport codes for display
    airport_codes = get_airport_codes()
    
    # Apply trip type filter if specified
    if trip_type_filter == 'upcoming':
        filtered_bookings = upcoming_bookings
    elif trip_type_filter == 'past':
        filtered_bookings = past_bookings
    elif trip_type_filter == 'completed':
        filtered_bookings = completed_bookings
    elif trip_type_filter == 'cancelled':
        filtered_bookings = cancelled_bookings
    else:
        filtered_bookings = all_bookings
    
    context = {
        'all_bookings': filtered_bookings,
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings,
        'upcoming_count': upcoming_bookings.count(),
        'past_count': past_bookings.count(),
        'completed_count': completed_bookings.count(),
        'cancelled_count': cancelled_bookings.count(),
        'total_count': all_bookings.count(),
        'from_date': from_date_str,
        'to_date': to_date_str,
        'trip_type_filter': trip_type_filter,
        'airport_codes': airport_codes,
        'today': today,
    }
    
    return render(request, 'my_trips.html', context)


@login_required
def cancel_booking(request, booking_id):
    """Cancel a booking"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status == Booking.Status.CONFIRMED:
        # Return seats to schedule
        schedule = booking.schedule
        seats_to_return = booking.passengers.count()
        schedule.available_seats += seats_to_return
        schedule.save()
        
        # Update booking status
        booking.status = Booking.Status.CANCELLED
        booking.save()
        messages.success(request, 'Your booking has been cancelled.')
    else:
        messages.error(request, 'This booking cannot be cancelled.')
    
    return redirect('dashboard')


@login_required
def payment_page(request, booking_id):
    """Payment page with Razorpay integration and wallet payment option"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Check if booking is already paid
    if booking.payment_status == Booking.PaymentStatus.PAID:
        messages.info(request, 'This booking is already paid.')
        return redirect('booking_confirmation', booking_id=booking.id)
    
    # Handle wallet payment if requested
    if request.method == 'POST' and request.POST.get('payment_method') in ['od_wallet', 'cash_balance']:
        payment_method = request.POST.get('payment_method')
        try:
            if payment_method == 'od_wallet':
                # OD Wallet payment (admin controlled)
                wallet = ODWallet.objects.get(user=request.user, is_active=True)
                wallet_type = 'OD Wallet'
            else:
                # Cash Balance Wallet payment (user self-recharge)
                wallet = CashBalanceWallet.objects.get(user=request.user)
                wallet_type = 'Cash Balance'
            
            if wallet.balance >= booking.total_amount:
                # Deduct from wallet
                wallet.deduct_balance(
                    amount=booking.total_amount,
                    transaction_type='payment',
                    description=f'Payment for booking {booking.booking_reference}',
                    reference_id=booking.booking_reference
                )
                
                # Confirm booking
                booking.payment_status = Booking.PaymentStatus.PAID
                booking.status = Booking.Status.CONFIRMED
                
                # Update schedule - reduce available seats
                seats_booked = booking.passengers.count() or 1
                if booking.schedule.available_seats >= seats_booked:
                    booking.schedule.available_seats -= seats_booked
                    booking.schedule.save()
                
                booking.save()
                
                messages.success(request, f'Payment successful using {wallet_type}! Booking confirmed: {booking.booking_reference}')
                return redirect('booking_confirmation', booking_id=booking.id)
            else:
                messages.error(request, f'Insufficient {wallet_type} balance. Your balance: ₹{wallet.balance}, Required: ₹{booking.total_amount}')
        except ODWallet.DoesNotExist:
            messages.error(request, 'OD Wallet is not available or not activated.')
        except CashBalanceWallet.DoesNotExist:
            messages.error(request, 'Cash Balance Wallet is not available.')
        except Exception as e:
            messages.error(request, f'Wallet payment failed: {str(e)}')
    
    # Handle skip payment (for testing)
    if request.method == 'POST' and request.POST.get('payment_method') == 'skip':
        # For testing: confirm booking without payment
        booking.payment_status = Booking.PaymentStatus.PAID
        booking.status = Booking.Status.CONFIRMED
        
        # Update schedule - reduce available seats
        seats_booked = booking.passengers.count() or 1
        if booking.schedule.available_seats >= seats_booked:
            booking.schedule.available_seats -= seats_booked
            booking.schedule.save()
        
        booking.save()
        
        messages.success(request, f'Booking confirmed: {booking.booking_reference} (Payment skipped for testing)')
        return redirect('booking_confirmation', booking_id=booking.id)
    
    # Get OD Wallet information for payment page
    od_wallet = None
    od_wallet_balance = Decimal('0')
    can_use_od_wallet = False
    try:
        od_wallet = ODWallet.objects.get(user=request.user, is_active=True)
        od_wallet_balance = od_wallet.balance
        can_use_od_wallet = od_wallet.balance >= booking.total_amount
    except ODWallet.DoesNotExist:
        pass
    
    # Get Cash Balance Wallet information for payment page
    cash_balance_wallet = None
    cash_balance = Decimal('0')
    can_use_cash_balance = False
    try:
        cash_balance_wallet = CashBalanceWallet.objects.get(user=request.user)
        cash_balance = cash_balance_wallet.balance
        can_use_cash_balance = cash_balance_wallet.balance >= booking.total_amount
    except CashBalanceWallet.DoesNotExist:
        # Auto-create cash balance wallet if it doesn't exist
        cash_balance_wallet = CashBalanceWallet.objects.create(user=request.user)
        cash_balance = Decimal('0')
    
    # ========== PAYMENT GATEWAY COMMENTED FOR TESTING ==========
    # Check if Razorpay is configured
    # razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
    # razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
    
    # Always show payment page with wallet option (if available)
    # Get comprehensive airport codes
    airport_codes = get_airport_codes()
    
    context = {
        'booking': booking,
        'airport_codes': airport_codes,
        'od_wallet': od_wallet,
        'od_wallet_balance': od_wallet_balance,
        'can_use_od_wallet': can_use_od_wallet,
        'cash_balance_wallet': cash_balance_wallet,
        'cash_balance': cash_balance,
        'can_use_cash_balance': can_use_cash_balance,
    }
    return render(request, 'payment.html', context)
    
    # ========== COMMENTED RAZORPAY CODE (UNCOMMENT WHEN READY FOR PRODUCTION) ==========
    # # Initialize Razorpay client
    # try:
    #     client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
    # except Exception as e:
    #     # If Razorpay initialization fails, skip payment and confirm directly
    #     booking.payment_status = Booking.PaymentStatus.PAID
    #     booking.status = Booking.Status.CONFIRMED
    #     
    #     seats_booked = booking.passengers.count() or 1
    #     if booking.schedule.available_seats >= seats_booked:
    #         booking.schedule.available_seats -= seats_booked
    #         booking.schedule.save()
    #     
    #     booking.save()
    #     
    #     messages.success(request, f'Booking confirmed: {booking.booking_reference} (Payment gateway unavailable - booking confirmed directly)')
    #     return redirect('booking_confirmation', booking_id=booking.id)
    # 
    # # Create order
    # amount_in_paise = int(booking.total_amount * 100)  # Convert to paise
    # order_data = {
    #     'amount': amount_in_paise,
    #     'currency': 'INR',
    #     'receipt': booking.booking_reference,
    #     'notes': {
    #         'booking_id': booking.id,
    #         'booking_reference': booking.booking_reference,
    #     }
    # }
    # 
    # try:
    #     razorpay_order = client.order.create(data=order_data)
    #     order_id = razorpay_order['id']
    #     
    #     # Store order_id in booking
    #     if not booking.notes:
    #         booking.notes = json.dumps({'razorpay_order_id': order_id})
    #     else:
    #         notes = json.loads(booking.notes) if booking.notes else {}
    #         notes['razorpay_order_id'] = order_id
    #         booking.notes = json.dumps(notes)
    #     booking.save()
    #     
    # except Exception as e:
    #     # If order creation fails, skip payment and confirm directly
    #     booking.payment_status = Booking.PaymentStatus.PAID
    #     booking.status = Booking.Status.CONFIRMED
    #     
    #     seats_booked = booking.passengers.count() or 1
    #     if booking.schedule.available_seats >= seats_booked:
    #         booking.schedule.available_seats -= seats_booked
    #         booking.schedule.save()
    #     
    #     booking.save()
    #     
    #     messages.success(request, f'Booking confirmed: {booking.booking_reference} (Payment gateway error - booking confirmed directly)')
    #     return redirect('booking_confirmation', booking_id=booking.id)
    # 
    # # Get comprehensive airport codes
    # airport_codes = get_airport_codes()
    # 
    # context = {
    #     'booking': booking,
    #     'razorpay_key_id': razorpay_key_id,
    #     'order_id': order_id,
    #     'amount': amount_in_paise,
    #     'airport_codes': airport_codes,
    #     'wallet': wallet,
    #     'wallet_balance': wallet_balance,
    #     'can_use_wallet': can_use_wallet,
    # }
    # return render(request, 'payment.html', context)


@login_required
@require_POST
def payment_success(request):
    """Handle successful payment callback"""
    # ========== PAYMENT GATEWAY COMMENTED FOR TESTING ==========
    # payment_id = request.POST.get('razorpay_payment_id')
    # order_id = request.POST.get('razorpay_order_id')
    # signature = request.POST.get('razorpay_signature')
    # 
    # # Verify payment signature
    # razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_xxxxxxxxxxxxx')
    # razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'xxxxxxxxxxxxxxxxxxxxx')
    # client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
    # 
    # try:
    #     # Find booking by order_id
    #     bookings = Booking.objects.filter(notes__icontains=order_id)
    #     booking = None
    #     for b in bookings:
    #         try:
    #             notes = json.loads(b.notes) if b.notes else {}
    #             if notes.get('razorpay_order_id') == order_id:
    #                 booking = b
    #                 break
    #         except:
    #             continue
    #     
    #     if not booking:
    #         messages.error(request, 'Booking not found.')
    #         return redirect('dashboard')
    #     
    #     # Verify signature
    #     params_dict = {
    #         'razorpay_order_id': order_id,
    #         'razorpay_payment_id': payment_id,
    #         'razorpay_signature': signature
    #     }
    #     
    #     client.utility.verify_payment_signature(params_dict)
    #     
    #     # Update booking status
    #     booking.payment_status = Booking.PaymentStatus.PAID
    #     booking.status = Booking.Status.CONFIRMED
    #     
    #     # Update notes with payment info
    #     notes = json.loads(booking.notes) if booking.notes else {}
    #     notes['razorpay_payment_id'] = payment_id
    #     notes['razorpay_order_id'] = order_id
    #     booking.notes = json.dumps(notes)
    #     
    #     # Update schedule - reduce available seats
    #     seats_booked = booking.passengers.count()
    #     booking.schedule.available_seats -= seats_booked
    #     booking.schedule.save()
    #     
    #     booking.save()
    #     
    #     messages.success(request, f'Payment successful! Booking confirmed: {booking.booking_reference}')
    #     return redirect('booking_confirmation', booking_id=booking.id)
    #     
    # except razorpay.errors.SignatureVerificationError:
    #     messages.error(request, 'Payment verification failed.')
    #     return redirect('payment_failed')
    # except Exception as e:
    #     messages.error(request, f'Payment processing error: {str(e)}')
    #     return redirect('payment_failed')
    
    # FOR TESTING: Direct confirmation without payment gateway
    messages.info(request, 'Payment gateway is disabled for testing. Please use the booking flow directly.')
    return redirect('dashboard')


@login_required
def payment_failed(request):
    """Payment failed page"""
    return render(request, 'payment_failed.html')

@login_required
def wallet_recharge(request):
    """Cash Balance Wallet recharge page - User self-recharge (direct access for everyone)"""
    # Get or create cash balance wallet for user (auto-created for all users)
    wallet, created = CashBalanceWallet.objects.get_or_create(user=request.user)
    
    # ========== PAYMENT GATEWAY COMMENTED FOR TESTING ==========
    # Handle successful payment callback
    # if request.method == 'POST' and request.POST.get('razorpay_payment_id'):
    #     payment_id = request.POST.get('razorpay_payment_id')
    #     order_id = request.POST.get('razorpay_order_id')
    #     signature = request.POST.get('razorpay_signature')
    #     amount = request.POST.get('amount')
    #     
    #     # Verify payment signature
    #     razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
    #     razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
    #     
    #     if not razorpay_key_id or not razorpay_key_secret:
    #         messages.error(request, 'Payment gateway not configured.')
    #         return redirect('wallet_recharge')
    #     
    #     try:
    #         client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
    #         
    #         # Verify signature
    #         params_dict = {
    #             'razorpay_order_id': order_id,
    #             'razorpay_payment_id': payment_id,
    #             'razorpay_signature': signature
    #         }
    #         
    #         client.utility.verify_payment_signature(params_dict)
    #         
    #         # Get amount from session or order
    #         recharge_amount = Decimal(request.session.get('wallet_recharge_amount', amount)) / 100 if amount else Decimal('0')
    #         description = request.session.get('wallet_recharge_description', 'Wallet Recharge via UPI/Card')
    #         
    #         # Check if adding this amount would exceed max balance
    #         if (wallet.balance + recharge_amount) > wallet.max_balance:
    #             messages.error(request, f'Recharge would exceed maximum balance limit of ₹{wallet.max_balance}')
    #         else:
    #             # Add balance to wallet
    #             wallet.add_balance(
    #                 amount=recharge_amount,
    #                 transaction_type='recharge',
    #                 description=description,
    #                 reference_id=payment_id
    #             )
    #             messages.success(request, f'Wallet recharged successfully! New balance: ₹{wallet.balance}')
    #             
    #             # Clear session
    #             if 'wallet_recharge_amount' in request.session:
    #                 del request.session['wallet_recharge_amount']
    #             if 'wallet_recharge_description' in request.session:
    #                 del request.session['wallet_recharge_description']
    #             
    #             return redirect('wallet_history')
    #             
    #     except razorpay.errors.SignatureVerificationError:
    #         messages.error(request, 'Payment verification failed. Please try again.')
    #     except Exception as e:
    #         messages.error(request, f'Recharge failed: {str(e)}')
    
    # Handle form submission - FOR TESTING: Directly add balance without payment gateway
    if request.method == 'POST':
        form = WalletRechargeForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            description = form.cleaned_data.get('description', 'Wallet Recharge (Testing Mode)')
            
            # Check if adding this amount would exceed max balance
            if (wallet.balance + amount) > wallet.max_balance:
                messages.error(request, f'Recharge would exceed maximum balance limit of ₹{wallet.max_balance}')
                form = WalletRechargeForm(initial={'amount': amount, 'description': description})
            else:
                # FOR TESTING: Directly add balance without payment gateway
                wallet.add_balance(
                    amount=amount,
                    transaction_type='recharge',
                    description=description,
                    reference_id=f'TEST_{int(timezone.now().timestamp())}'
                )
                messages.success(request, f'Wallet recharged successfully! New balance: ₹{wallet.balance} (Testing mode - no payment gateway)')
                return redirect('wallet_history')
        else:
            form = WalletRechargeForm()
    
    # ========== COMMENTED RAZORPAY CODE (UNCOMMENT WHEN READY FOR PRODUCTION) ==========
    # # Handle form submission - create Razorpay order
    # elif request.method == 'POST':
    #     form = WalletRechargeForm(request.POST)
    #     if form.is_valid():
    #         amount = form.cleaned_data['amount']
    #         description = form.cleaned_data.get('description', 'Wallet Recharge')
    #         
    #         # Check if adding this amount would exceed max balance
    #         if (wallet.balance + amount) > wallet.max_balance:
    #             messages.error(request, f'Recharge would exceed maximum balance limit of ₹{wallet.max_balance}')
    #             form = WalletRechargeForm(initial={'amount': amount, 'description': description})
    #         else:
    #             # Store in session for after payment
    #             request.session['wallet_recharge_amount'] = str(amount)
    #             request.session['wallet_recharge_description'] = description
    #             
    #             # Initialize Razorpay client
    #             razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
    #             razorpay_key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
    #             
    #             if not razorpay_key_id or not razorpay_key_secret:
    #                 messages.error(request, 'Payment gateway not configured. Please contact support.')
    #                 form = WalletRechargeForm(initial={'amount': amount, 'description': description})
    #             else:
    #                 try:
    #                     client = razorpay.Client(auth=(razorpay_key_id, razorpay_key_secret))
    #                     
    #                     # Create order
    #                     amount_in_paise = int(amount * 100)  # Convert to paise
    #                     order_data = {
    #                         'amount': amount_in_paise,
    #                         'currency': 'INR',
    #                         'receipt': f'WALLET_{request.user.id}_{int(timezone.now().timestamp())}',
    #                         'notes': {
    #                             'user_id': request.user.id,
    #                             'type': 'wallet_recharge',
    #                             'description': description,
    #                         }
    #                     }
    #                     
    #                     razorpay_order = client.order.create(data=order_data)
    #                     order_id = razorpay_order['id']
    #                     
    #                     context = {
    #                         'form': form,
    #                         'wallet': wallet,
    #                         'wallet_balance': wallet.balance,
    #                         'max_balance': wallet.max_balance,
    #                         'razorpay_key_id': razorpay_key_id,
    #                         'order_id': order_id,
    #                         'amount': amount_in_paise,
    #                         'recharge_amount': amount,
    #                     }
    #                     return render(request, 'wallet_recharge.html', context)
    #                     
    #                 except Exception as e:
    #                     messages.error(request, f'Payment gateway error: {str(e)}')
    #                     form = WalletRechargeForm(initial={'amount': amount, 'description': description})
    #     else:
    #         form = WalletRechargeForm()
    else:
        form = WalletRechargeForm()
    
    context = {
        'form': form,
        'wallet': wallet,
        'wallet_balance': wallet.balance,
        'max_balance': wallet.max_balance,
    }
    return render(request, 'wallet_recharge.html', context)

@login_required
def wallet_history(request):
    """Wallet transaction history page - supports both OD Wallet and Cash Balance Wallet"""
    wallet_type = request.GET.get('type', 'cash_balance')  # Default to cash balance
    
    if wallet_type == 'od':
        # OD Wallet history (only if active)
        try:
            wallet = ODWallet.objects.get(user=request.user, is_active=True)
            transactions = wallet.transactions.all().order_by('-created_at')[:50]  # Last 50 transactions
            wallet_balance = wallet.balance
            wallet_name = 'OD Wallet'
        except ODWallet.DoesNotExist:
            messages.info(request, 'OD Wallet is not available or not activated.')
            return redirect('dashboard')
    else:
        # Cash Balance Wallet history (direct access for everyone)
        wallet, created = CashBalanceWallet.objects.get_or_create(user=request.user)
        transactions = wallet.transactions.all().order_by('-created_at')[:50]  # Last 50 transactions
        wallet_balance = wallet.balance
        wallet_name = 'Cash Balance'
    
    context = {
        'wallet': wallet,
        'wallet_balance': wallet_balance,
        'transactions': transactions,
        'wallet_type': wallet_type,
        'wallet_name': wallet_name,
    }
    
    return render(request, 'wallet_history.html', context)

@login_required
def group_request(request):
    """Group booking request form for B2B customers (more than 9 passengers)"""
    if request.method == 'POST':
        try:
            # Get form data
            contact_name = request.POST.get('contact_name', '').strip()
            contact_email = request.POST.get('contact_email', '').strip()
            contact_phone = request.POST.get('contact_phone', '').strip()
            company_name = request.POST.get('company_name', '').strip()
            origin = request.POST.get('origin', '').strip()
            destination = request.POST.get('destination', '').strip()
            departure_date_str = request.POST.get('departure_date', '').strip()
            return_date_str = request.POST.get('return_date', '').strip()
            trip_type = request.POST.get('trip_type', 'one_way')
            travel_class = request.POST.get('travel_class', 'economy')
            number_of_passengers = int(request.POST.get('number_of_passengers', 10))
            adults = int(request.POST.get('adults', 0))
            children = int(request.POST.get('children', 0))
            infants = int(request.POST.get('infants', 0))
            special_requirements = request.POST.get('special_requirements', '').strip()
            additional_notes = request.POST.get('additional_notes', '').strip()
            
            # Validation
            if not contact_name or not contact_email or not contact_phone:
                messages.error(request, 'Please fill in all required contact fields.')
                return redirect('group_request')
            
            if not origin or not destination:
                messages.error(request, 'Please specify origin and destination.')
                return redirect('group_request')
            
            if not departure_date_str:
                messages.error(request, 'Please select a departure date.')
                return redirect('group_request')
            
            if number_of_passengers < 10:
                messages.error(request, 'Group requests require at least 10 passengers.')
                return redirect('group_request')
            
            # Parse dates
            departure_date = datetime.strptime(departure_date_str, '%Y-%m-%d').date()
            return_date = None
            if return_date_str and trip_type == 'return':
                return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
                if return_date <= departure_date:
                    messages.error(request, 'Return date must be after departure date.')
                    return redirect('group_request')
            
            if departure_date < date.today():
                messages.error(request, 'Departure date cannot be in the past.')
                return redirect('group_request')
            
            # Create group request
            group_request_obj = GroupRequest.objects.create(
                user=request.user,
                contact_name=contact_name,
                contact_email=contact_email,
                contact_phone=contact_phone,
                company_name=company_name,
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                trip_type=trip_type,
                travel_class=travel_class,
                number_of_passengers=number_of_passengers,
                adults=adults,
                children=children,
                infants=infants,
                special_requirements=special_requirements,
                additional_notes=additional_notes,
                status=GroupRequest.Status.PENDING
            )
            
            # Redirect to thank you page
            return redirect('group_request_thanks', request_id=group_request_obj.id)
            
        except ValueError as e:
            messages.error(request, f'Invalid input: {str(e)}')
            return redirect('group_request')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('group_request')
    
    # GET request - show form
    airport_codes = get_airport_codes()
    today = date.today().strftime('%Y-%m-%d')
    min_return_date = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    context = {
        'airport_codes': airport_codes,
        'today': today,
        'min_return_date': min_return_date,
    }
    return render(request, 'group_request.html', context)

@login_required
def group_request_thanks(request, request_id):
    """Thank you page after submitting group request"""
    group_request_obj = get_object_or_404(GroupRequest, id=request_id, user=request.user)
    
    context = {
        'group_request': group_request_obj,
    }
    return render(request, 'group_request_thanks.html', context)

@login_required
@require_POST
def upload_profile_pdf(request):
    """Upload or update PDF document in user profile"""
    try:
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'full_name': request.user.get_full_name() or request.user.email.split('@')[0]}
        )
        pdf_type = request.POST.get('pdf_type')
        pdf_file = request.FILES.get('pdf_file')
        
        if not pdf_file:
            return JsonResponse({'success': False, 'error': 'No file provided'})
        
        # Validate file type
        if not pdf_file.name.lower().endswith('.pdf'):
            return JsonResponse({'success': False, 'error': 'Only PDF files are allowed'})
        
        # Validate file size (10MB max)
        if pdf_file.size > 10 * 1024 * 1024:
            return JsonResponse({'success': False, 'error': 'File size must be less than 10MB'})
        
        # Update the appropriate field
        if pdf_type == 'id_document':
            profile.id_document_pdf = pdf_file
        elif pdf_type == 'passport':
            profile.passport_pdf = pdf_file
        elif pdf_type == 'other_documents':
            profile.other_documents = pdf_file
        else:
            return JsonResponse({'success': False, 'error': 'Invalid PDF type'})
        
        profile.save()
        return JsonResponse({'success': True, 'message': 'PDF uploaded successfully'})
        
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profile not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def delete_profile_pdf(request):
    """Delete PDF document from user profile"""
    try:
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'full_name': request.user.get_full_name() or request.user.email.split('@')[0]}
        )
        pdf_type = request.POST.get('pdf_type')
        
        if pdf_type == 'id_document':
            if profile.id_document_pdf:
                profile.id_document_pdf.delete()
                profile.id_document_pdf = None
        elif pdf_type == 'passport':
            if profile.passport_pdf:
                profile.passport_pdf.delete()
                profile.passport_pdf = None
        elif pdf_type == 'other_documents':
            if profile.other_documents:
                profile.other_documents.delete()
                profile.other_documents = None
        else:
            messages.error(request, 'Invalid PDF type')
            return redirect('dashboard')
        
        profile.save()
        messages.success(request, 'PDF document deleted successfully')
        
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile not found')
    except Exception as e:
        messages.error(request, f'Error deleting PDF: {str(e)}')
    
    return redirect('dashboard')


@login_required
def booking_confirmation(request, booking_id):
    """Booking confirmation page after payment"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Get comprehensive airport codes
    airport_codes = get_airport_codes()
    
    context = {
        'booking': booking,
        'airport_codes': airport_codes,
    }
    return render(request, 'booking_confirmation.html', context)


def _generate_ticket_pdf(booking, hide_fare=False):
    """Helper function to generate ticket PDF with optional fare hiding"""
    from io import BytesIO
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#0ea5e9'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph('Flight Ticket', title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Booking Reference
    ref_style = ParagraphStyle(
        'RefStyle',
        parent=styles['Normal'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    story.append(Paragraph(f'Booking Reference: <b>{booking.booking_reference}</b>', ref_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Outbound Flight Details
    flight_data = [
        ['Outbound Flight Details', ''],
        ['Route', f"{booking.schedule.route.from_location} → {booking.schedule.route.to_location}"],
        ['Flight Number', booking.schedule.route.carrier_number],
        ['Departure Date', booking.schedule.departure_date.strftime('%d %B %Y')],
        ['Departure Time', booking.schedule.route.departure_time.strftime('%H:%M')],
        ['Arrival Time', booking.schedule.route.arrival_time.strftime('%H:%M')],
        ['Duration', booking.schedule.route.formatted_duration],
    ]
    
    # Add terminal information if available
    if booking.schedule.route.departure_terminal:
        flight_data.append(['Departure Terminal', booking.schedule.route.departure_terminal])
    if booking.schedule.route.arrival_terminal:
        flight_data.append(['Arrival Terminal', booking.schedule.route.arrival_terminal])
    
    flight_table = Table(flight_data, colWidths=[2*inch, 4*inch])
    flight_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    story.append(flight_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Return Flight Details (if return trip)
    if booking.trip_type == 'return' and booking.return_schedule:
        return_flight_data = [
            ['Return Flight Details', ''],
            ['Route', f"{booking.return_schedule.route.from_location} → {booking.return_schedule.route.to_location}"],
            ['Flight Number', booking.return_schedule.route.carrier_number],
            ['Departure Date', booking.return_schedule.departure_date.strftime('%d %B %Y')],
            ['Departure Time', booking.return_schedule.route.departure_time.strftime('%H:%M')],
            ['Arrival Time', booking.return_schedule.route.arrival_time.strftime('%H:%M')],
            ['Duration', booking.return_schedule.route.formatted_duration],
        ]
        
        # Add terminal information if available
        if booking.return_schedule.route.departure_terminal:
            return_flight_data.append(['Departure Terminal', booking.return_schedule.route.departure_terminal])
        if booking.return_schedule.route.arrival_terminal:
            return_flight_data.append(['Arrival Terminal', booking.return_schedule.route.arrival_terminal])
        
        return_flight_table = Table(return_flight_data, colWidths=[2*inch, 4*inch])
        return_flight_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(return_flight_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Passenger Details
    story.append(Paragraph('Passenger Details', styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    
    passengers = booking.passengers.all()
    passenger_data = [['Name', 'Date of Birth', 'Gender', 'Passport Number']]
    
    for passenger in passengers:
        passenger_data.append([
            passenger.full_name,
            passenger.date_of_birth.strftime('%d %b %Y') if passenger.date_of_birth else 'N/A',
            passenger.get_gender_display(),
            passenger.passport_number or 'N/A'
        ])
    
    passenger_table = Table(passenger_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1.5*inch])
    passenger_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(passenger_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Payment Details (only if not hiding fare)
    if not hide_fare:
        payment_data = [
            ['Payment Details', ''],
            ['Base Fare', f'₹{booking.base_fare:.2f}'],
            ['Taxes & Fees', f'₹{booking.tax_amount:.2f}'],
            ['Total Amount', f'₹{booking.total_amount:.2f}'],
            ['Payment Status', booking.get_payment_status_display()],
        ]
        
        payment_table = Table(payment_data, colWidths=[2*inch, 4*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(payment_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph('This is an electronic ticket. Please carry a valid ID proof to the airport.', footer_style))
    story.append(Paragraph('For support, contact: support@safarzone.com | +91 98765 43210', footer_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


@login_required
@xframe_options_sameorigin
def download_ticket_pdf(request, booking_id):
    """Generate and download PDF ticket"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Only allow download for confirmed and paid bookings
    if booking.status != Booking.Status.CONFIRMED or booking.payment_status != Booking.PaymentStatus.PAID:
        messages.error(request, 'Ticket can only be downloaded for confirmed and paid bookings.')
        return redirect('dashboard')
    
    # Check if hiding fare
    hide_fare = request.GET.get('hide_fare', 'false').lower() == 'true'
    
    # Generate PDF
    buffer = _generate_ticket_pdf(booking, hide_fare=hide_fare)
    
    # Create PDF response
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    # Check if viewing inline (for iframe) or downloading
    view_mode = request.GET.get('view', 'false').lower() == 'true'
    if view_mode:
        response['Content-Disposition'] = f'inline; filename="ticket_{booking.booking_reference}.pdf"'
        # Allow iframe embedding for viewing
        response['X-Frame-Options'] = 'SAMEORIGIN'
    else:
        response['Content-Disposition'] = f'attachment; filename="ticket_{booking.booking_reference}.pdf"'
    
    return response


@login_required
def print_ticket_pdf(request, booking_id):
    """Print ticket PDF without fare"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status != Booking.Status.CONFIRMED or booking.payment_status != Booking.PaymentStatus.PAID:
        messages.error(request, 'Ticket can only be printed for confirmed and paid bookings.')
        return redirect('dashboard')
    
    # Generate PDF without fare
    buffer = _generate_ticket_pdf(booking, hide_fare=True)
    
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="ticket_{booking.booking_reference}_nofare.pdf"'
    return response


@login_required
@require_POST
def email_ticket(request, booking_id):
    """Email ticket PDF with or without fare"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status != Booking.Status.CONFIRMED or booking.payment_status != Booking.PaymentStatus.PAID:
        return JsonResponse({'success': False, 'message': 'Ticket can only be emailed for confirmed and paid bookings.'})
    
    hide_fare = request.POST.get('hide_fare', 'false').lower() == 'true'
    recipient_email = request.POST.get('email', booking.contact_email or request.user.email)
    
    try:
        from django.core.mail import EmailMessage
        from django.conf import settings
        
        # Generate PDF
        buffer = _generate_ticket_pdf(booking, hide_fare=hide_fare)
        
        # Create email
        subject = f'Your Flight Ticket - {booking.booking_reference}'
        body = f"""
Dear {booking.contact_email or request.user.email},

Please find attached your flight ticket for booking reference: {booking.booking_reference}

Flight Details:
- Route: {booking.schedule.route.from_location} → {booking.schedule.route.to_location}
- Flight Number: {booking.schedule.route.carrier_number}
- Departure Date: {booking.schedule.departure_date.strftime('%d %B %Y')}
- Departure Time: {booking.schedule.route.departure_time.strftime('%H:%M')}

Please carry a valid ID proof to the airport.

For support, contact: support@safarzone.com | +91 98765 43210

Thank you for choosing Safar Zone Travels!
        """
        
        email = EmailMessage(
            subject,
            body,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@safarzone.com'),
            [recipient_email]
        )
        
        email.attach(
            f'ticket_{booking.booking_reference}.pdf',
            buffer.read(),
            'application/pdf'
        )
        email.send()
        
        return JsonResponse({
            'success': True,
            'message': f'Ticket has been sent to {recipient_email} successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Failed to send email: {str(e)}'
        })


@login_required
@require_POST
def edit_booking_fare(request, booking_id):
    """Edit booking fare"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status != Booking.Status.CONFIRMED:
        return JsonResponse({'success': False, 'message': 'Can only edit fare for confirmed bookings.'})
    
    try:
        new_base_fare = Decimal(request.POST.get('base_fare', booking.base_fare))
        new_tax_amount = Decimal(request.POST.get('tax_amount', booking.tax_amount))
        new_total = new_base_fare + new_tax_amount
        
        if new_base_fare < 0 or new_tax_amount < 0:
            return JsonResponse({'success': False, 'message': 'Fare amounts cannot be negative.'})
        
        booking.base_fare = new_base_fare
        booking.tax_amount = new_tax_amount
        booking.total_amount = new_total
        booking.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Fare updated successfully!',
            'new_total': str(new_total)
        })
    except (ValueError, TypeError) as e:
        return JsonResponse({'success': False, 'message': f'Invalid fare amount: {str(e)}'})


@require_http_methods(['GET', 'POST'])
def user_login(request):
    """Handle user login with email and password"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
                # Get user's full name safely (create profile if it doesn't exist)
                try:
                    profile = user.profile
                    full_name = profile.full_name if profile.full_name else user.email
                except UserProfile.DoesNotExist:
                    # Create profile if it doesn't exist
                    UserProfile.objects.create(
                        user=user,
                        full_name=user.get_full_name() or user.email.split('@')[0]
                    )
                    full_name = user.get_full_name() or user.email.split('@')[0]
                
                messages.success(request, f'Welcome back, {full_name}!')
                next_url = request.POST.get('next') or 'dashboard'
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid email or password')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = UserLoginForm()
    
    return render(request, 'login.html', {'form': form})

@csrf_exempt
def send_otp(request):
    """Send OTP to email address for account verification"""
    if request.method == 'POST':
        import json
        from django.http import JsonResponse
        from django.core.mail import send_mail
        from django.conf import settings
        import random
        
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
            
            # Validate email
            if not email or '@' not in email:
                return JsonResponse({'success': False, 'message': 'Invalid email address.'})
            
            # Check if email is already registered
            User = get_user_model()
            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'message': 'This email is already registered.'})
            
            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))
            
            # Delete old OTPs for this email
            OTPVerification.objects.filter(email=email, is_verified=False).delete()
            
            # Create new OTP (expires in 10 minutes)
            expires_at = timezone.now() + timedelta(minutes=10)
            otp_obj = OTPVerification.objects.create(
                email=email,
                otp=otp,
                expires_at=expires_at
            )
            
            # Send OTP via Email
            try:
                subject = 'Your OTP for Safar Zone Account Verification'
                message = f'''
Hello,

Thank you for registering with Safar Zone Travels!

Your OTP for account verification is: {otp}

This OTP is valid for 10 minutes.

If you did not request this OTP, please ignore this email.

Best regards,
Safar Zone Travels Team
                '''
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@safarzone.com')
                
                send_mail(
                    subject,
                    message,
                    from_email,
                    [email],
                    fail_silently=False,
                )
            except Exception as e:
                # If email fails, still return success but log the error
                print(f"Email sending failed: {str(e)}")
                # For development, print OTP to console
                print(f"OTP for {email}: {otp}")
            
            return JsonResponse({
                'success': True, 
                'message': f'OTP sent successfully to {email}! Please check your inbox.',
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@csrf_exempt
def verify_otp(request):
    """Verify OTP for email address"""
    if request.method == 'POST':
        import json
        from django.http import JsonResponse
        
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
            otp = data.get('otp', '').strip()
            
            if not email or not otp:
                return JsonResponse({'success': False, 'message': 'Email and OTP are required.'})
            
            # Find the latest unverified OTP for this email
            otp_obj = OTPVerification.objects.filter(
                email=email,
                is_verified=False
            ).order_by('-created_at').first()
            
            if not otp_obj:
                return JsonResponse({'success': False, 'message': 'No OTP found. Please request a new OTP.'})
            
            if otp_obj.is_expired():
                return JsonResponse({'success': False, 'message': 'OTP has expired. Please request a new OTP.'})
            
            if otp_obj.attempts >= 3:
                return JsonResponse({'success': False, 'message': 'Maximum attempts exceeded. Please request a new OTP.'})
            
            # Verify OTP
            if otp_obj.verify(otp):
                # Store verification in session with email and aadhar
                request.session['email_verified'] = email
                request.session['otp_verified_at'] = timezone.now().isoformat()
                return JsonResponse({'success': True, 'message': 'OTP verified successfully! You can now create your account.'})
            else:
                remaining_attempts = 3 - otp_obj.attempts
                return JsonResponse({
                    'success': False, 
                    'message': f'Invalid OTP. {remaining_attempts} attempt(s) remaining.'
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def user_signup(request):
    """Handle new user registration (OTP verification disabled for now)"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                # Save the user (which also creates the profile)
                user = form.save()
                
                # Log the user in
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'Account created successfully! Welcome to Safar Zone Travels.')
                return redirect('dashboard')
                
            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
                # Log the error for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Error during user registration: {str(e)}')
        else:
            # Form has errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = UserRegisterForm()
    
    return render(request, 'signup.html', {
        'form': form
    })


@login_required
def user_logout(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('homepage')


# Admin Views
def is_staff_user(user):
    return user.is_staff


@login_required
@user_passes_test(is_staff_user)
def admin_schedules(request):
    """Admin schedule management"""
    schedule_list = Schedule.objects.select_related('route').all().order_by('-departure_date')
    routes = Route.objects.all()
    
    # Stats
    total_routes = Route.objects.count()
    active_schedules = Schedule.objects.filter(is_active=True).count()
    total_seats = Schedule.objects.aggregate(Sum('available_seats'))['available_seats__sum'] or 0
    today_bookings = Booking.objects.filter(created_at__date=timezone.now().date()).count()
    
    # Get comprehensive airport codes
    airport_codes = get_airport_codes()
    
    context = {
        'schedule_list': schedule_list,
        'routes': routes,
        'total_routes': total_routes,
        'active_schedules': active_schedules,
        'total_seats': total_seats,
        'today_bookings': today_bookings,
        'airport_codes': airport_codes,
    }
    return render(request, 'admin_schedules.html', context)


@login_required
@user_passes_test(is_staff_user)
def add_schedule(request):
    """Add new schedule"""
    if request.method == 'POST':
        route_id = request.POST.get('route')
        departure_date = request.POST.get('departure_date')
        arrival_date = request.POST.get('arrival_date')
        total_seats = int(request.POST.get('total_seats', 0))
        price = float(request.POST.get('price', 0))
        is_active = request.POST.get('is_active') == 'on'
        notes = request.POST.get('notes', '')
        
        route = get_object_or_404(Route, id=route_id)
        
        # Create new schedule
        Schedule.objects.create(
            route=route,
            departure_date=departure_date,
            arrival_date=arrival_date,
            total_seats=total_seats,
            available_seats=total_seats,  # Initially all seats are available
            price=price,
            is_active=is_active,
            notes=notes
        )
        messages.success(request, 'Schedule added successfully!')
    
    return redirect('admin_schedules')


@login_required
@user_passes_test(is_staff_user)
def delete_schedule(request, schedule_id):
    """Delete schedule"""
    if request.method == 'POST':
        schedule = get_object_or_404(Schedule, id=schedule_id)
        schedule.delete()
        messages.success(request, 'Schedule deleted successfully!')
    
    return redirect('admin_schedules')


@login_required
def admin_packages(request):
    """Admin package management"""
    packages = Package.objects.all().order_by('-is_featured', '-created_at')
    
    context = {
        'packages': packages,
    }
    return render(request, 'admin_packages.html', context)


@login_required
@user_passes_test(is_staff_user)
def add_package(request):
    """Add new package"""
    if request.method == 'POST':
        destination = request.POST.get('destination')
        title = request.POST.get('title')
        description = request.POST.get('description')
        price = request.POST.get('price')
        duration = request.POST.get('duration')
        image_url = request.POST.get('image_url', '')
        is_featured = request.POST.get('is_featured') == 'true'
        
        Package.objects.create(
            destination=destination,
            title=title,
            description=description,
            price=price,
            duration=duration,
            image_url=image_url,
            is_featured=is_featured
        )
        messages.success(request, 'Package added successfully!')
    
    return redirect('admin_packages')


def apply_package(request, package_name=None):
    """Package application form - for applying to travel packages"""
    if request.method == 'POST':
        try:
            # Get form data
            package_name = request.POST.get('package_name', '').strip()
            destination = request.POST.get('destination', package_name).strip()
            full_name = request.POST.get('full_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            travel_date_str = request.POST.get('travel_date', '').strip()
            number_of_people = int(request.POST.get('number_of_people', 1))
            special_requests = request.POST.get('special_requests', '').strip()
            
            # Validate required fields
            if not all([package_name, full_name, email, phone]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('apply_package', package_name=package_name or '')
            
            # Parse travel date if provided
            travel_date = None
            if travel_date_str:
                try:
                    travel_date = datetime.strptime(travel_date_str, '%Y-%m-%d').date()
                except ValueError:
                    travel_date = None
            
            # Get user IP and user agent
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Create package application
            application = PackageApplication.objects.create(
                package_name=package_name,
                destination=destination,
                user=request.user if request.user.is_authenticated else None,
                full_name=full_name,
                email=email,
                phone=phone,
                travel_date=travel_date,
                number_of_people=number_of_people,
                special_requests=special_requests,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            
            messages.success(request, f'Your application for {package_name} package has been submitted successfully! We will contact you soon.')
            return redirect('homepage')
            
        except Exception as e:
            messages.error(request, f'Error submitting application: {str(e)}')
            return redirect('apply_package', package_name=package_name or '')
    
    # GET request - show form
    # Default package destinations with images
    popular_packages = [
        {
            'name': 'Thailand', 
            'destination': 'Thailand',
            'image': 'https://images.unsplash.com/photo-1552465011-b4e21bf6e79a?w=800&h=600&fit=crop',
            'description': 'Experience the vibrant culture, stunning beaches, and delicious cuisine of Thailand'
        },
        {
            'name': 'Dubai', 
            'destination': 'Dubai',
            'image': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800&h=600&fit=crop',
            'description': 'Discover luxury, modern architecture, and desert adventures in Dubai'
        },
        {
            'name': 'Singapore', 
            'destination': 'Singapore',
            'image': 'https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=800&h=600&fit=crop',
            'description': 'Explore the perfect blend of culture, cuisine, and cutting-edge innovation'
        },
        {
            'name': 'Bali', 
            'destination': 'Bali',
            'image': 'https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?w=800&h=600&fit=crop',
            'description': 'Relax on pristine beaches and immerse in Balinese culture and spirituality'
        },
        {
            'name': 'Vietnam', 
            'destination': 'Vietnam',
            'image': 'https://images.unsplash.com/photo-1528127269322-539801943592?w=800&h=600&fit=crop',
            'description': 'Journey through rich history, breathtaking landscapes, and amazing food'
        },
    ]
    
    # Find the selected package
    selected_package = None
    if package_name:
        for pkg in popular_packages:
            if pkg['name'].lower() == package_name.lower():
                selected_package = pkg
                break
    
    # Pre-fill form if user is authenticated
    initial_data = {}
    if request.user.is_authenticated:
        initial_data['email'] = request.user.email
        if hasattr(request.user, 'profile') and request.user.profile:
            initial_data['full_name'] = request.user.profile.full_name or request.user.get_full_name()
            if hasattr(request.user.profile, 'phone'):
                initial_data['phone'] = request.user.profile.phone or request.user.phone
    
    context = {
        'package_name': package_name or '',
        'selected_package': selected_package,
        'popular_packages': popular_packages,
        'initial_data': initial_data,
        'today': date.today().isoformat(),
    }
    
    return render(request, 'apply_package.html', context)

@login_required
@user_passes_test(is_staff_user)
def delete_package(request, package_id):
    """Delete package"""
    if request.method == 'POST':
        package = get_object_or_404(Package, id=package_id)
        package.delete()
        messages.success(request, 'Package deleted successfully!')
    
    return redirect('admin_packages')
