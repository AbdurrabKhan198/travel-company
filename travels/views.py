from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, date, timedelta
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from .models import Schedule, Route, Booking, Package, UserProfile
from .forms import UserRegisterForm, UserLoginForm, ProfileUpdateForm
import random
import string
import json


def homepage(request):
    """Homepage with search and featured packages"""
    packages = Package.objects.filter(is_featured=True)[:6]
    
    # Get unique locations for search dropdowns
    origins = Route.objects.values_list('from_location', flat=True).distinct()
    destinations = Route.objects.values_list('to_location', flat=True).distinct()
    
    # Airport codes dictionary for major cities
    airport_codes = {
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
        'Dubai': 'DXB',
        'Singapore': 'SIN',
        'Bangkok': 'BKK',
        'London': 'LHR',
        'New York': 'JFK',
        'Paris': 'CDG',
        'Tokyo': 'NRT',
        'Sydney': 'SYD',
    }
    
    context = {
        'packages': packages,
        'origins': origins,
        'destinations': destinations,
        'today': date.today().isoformat(),
        'airport_codes': airport_codes,
    }
    return render(request, 'index.html', context)


def search_flights(request):
    """Search for available flights with enhanced functionality"""
    from_location = request.GET.get('from_location', '').strip()
    to_location = request.GET.get('to_location', '').strip()
    travel_date = request.GET.get('travel_date', '').strip()
    route_type = request.GET.get('route_type', '').strip()
    passengers = int(request.GET.get('passengers', 1))
    
    # Airport codes dictionary for major cities
    airport_codes = {
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
        'Dubai': 'DXB',
        'Singapore': 'SIN',
        'Bangkok': 'BKK',
        'London': 'LHR',
        'New York': 'JFK',
        'Paris': 'CDG',
        'Tokyo': 'NRT',
        'Sydney': 'SYD',
    }
    
    # Validate required fields
    if not from_location or not to_location:
        messages.error(request, 'Please select both origin and destination.')
        return redirect('homepage')
    
    if from_location == to_location:
        messages.error(request, 'Origin and destination cannot be the same.')
        return redirect('homepage')
    
    # Start with base query
    flights = Schedule.objects.select_related('route').filter(
        route__from_location=from_location,
        route__to_location=to_location,
        is_active=True
    )
    
    # Filter by route type if specified
    if route_type and route_type in dict(Route.ROUTE_TYPE_CHOICES):
        flights = flights.filter(route__route_type=route_type)
    
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
    
    # Get route information
    route_info = None
    if flights.exists():
        route_info = flights.first().route
    
    # Get airport codes for display
    from_airport_code = airport_codes.get(from_location, '')
    to_airport_code = airport_codes.get(to_location, '')
    
    context = {
        'flights': flights,
        'from_location': from_location,
        'to_location': to_location,
        'from_airport_code': from_airport_code,
        'to_airport_code': to_airport_code,
        'airport_codes': airport_codes,  # Pass the full dictionary for individual flights
        'travel_date': travel_date,
        'route_type': route_type,
        'passengers': passengers,
        'route_info': route_info,
        'total_flights': flights.count(),
    }
    return render(request, 'search.html', context)


@login_required
def booking_page(request, schedule_id):
    """Enhanced booking page for a specific flight with multiple passenger support"""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    passengers = int(request.GET.get('passengers', 1))
    
    # Ensure passengers doesn't exceed available seats
    if passengers > schedule.available_seats:
        passengers = schedule.available_seats
        messages.warning(request, f'Maximum {passengers} passengers can be booked for this flight.')
    
    if request.method == 'POST':
        # Process booking for multiple passengers
        seats_booked = int(request.POST.get('seats_booked', passengers))
        
        # Check availability
        if schedule.available_seats < seats_booked:
            messages.error(request, f'Not enough seats available! Only {schedule.available_seats} seats left.')
            return redirect('booking', schedule_id=schedule_id)
        
        # Generate booking reference
        booking_ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        # Calculate total amount
        total_amount = schedule.price * seats_booked
        
        # Get passenger details
        passenger_names = request.POST.getlist('passenger_name[]')
        passenger_ages = request.POST.getlist('passenger_age[]')
        passenger_genders = request.POST.getlist('passenger_gender[]')
        id_types = request.POST.getlist('id_type[]')
        id_last_4_digits_list = request.POST.getlist('id_last_4_digits[]')
        
        # Validate passenger details
        if len(passenger_names) != seats_booked:
            messages.error(request, 'Please fill in all passenger details.')
            return redirect('booking', schedule_id=schedule_id)
        
        # Create booking with primary passenger details
        booking = Booking.objects.create(
            user=request.user,
            schedule=schedule,
            booking_reference=booking_ref,
            passenger_name=passenger_names[0],  # Primary passenger
            passenger_age=passenger_ages[0],
            passenger_gender=passenger_genders[0],
            id_type=id_types[0],
            id_last_4_digits=id_last_4_digits_list[0],
            seats_booked=seats_booked,
            total_amount=total_amount,
            status='confirmed'
        )
        
        # Store additional passenger details in a JSON field or separate model
        # For now, we'll store it as a formatted string in the booking
        additional_passengers = []
        for i in range(1, seats_booked):
            additional_passengers.append({
                'name': passenger_names[i],
                'age': passenger_ages[i],
                'gender': passenger_genders[i],
                'id_type': id_types[i],
                'id_last_4': id_last_4_digits_list[i]
            })
        
        if additional_passengers:
            booking.additional_passengers = additional_passengers
            booking.save()
        
        # Update schedule
        schedule.available_seats -= seats_booked
        schedule.save()
        
        # Airport codes dictionary for confirmation page
        airport_codes = {
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
            'Dubai': 'DXB',
            'Singapore': 'SIN',
            'Bangkok': 'BKK',
            'London': 'LHR',
            'New York': 'JFK',
            'Paris': 'CDG',
            'Tokyo': 'NRT',
            'Sydney': 'SYD',
        }
        
        # Render confirmation page
        context = {
            'booking': booking,
            'airport_codes': airport_codes,
        }
        return render(request, 'booking_confirmation.html', context)
    
    # Airport codes dictionary for major cities
    airport_codes = {
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
        'Dubai': 'DXB',
        'Singapore': 'SIN',
        'Bangkok': 'BKK',
        'London': 'LHR',
        'New York': 'JFK',
        'Paris': 'CDG',
        'Tokyo': 'NRT',
        'Sydney': 'SYD',
    }
    
    context = {
        'inventory': inventory,
        'passengers': passengers,
        'passenger_range': range(1, passengers + 1),
        'airport_codes': airport_codes,
    }
    return render(request, 'booking.html', context)

def contact(request):
    return render(request, 'contact.html')

def about(request):
    return render(request, 'about.html')

@login_required
def dashboard(request):
    """User dashboard with bookings"""
    today = timezone.now().date()
    
    # Get all bookings
    all_bookings = Booking.objects.filter(user=request.user).select_related('schedule__route')
    
    upcoming_bookings = all_bookings.filter(
        schedule__departure_date__gte=today,
        status='confirmed'
    )
    
    past_bookings = all_bookings.filter(
        schedule__departure_date__lt=today,
        status='confirmed'
    )
    
    cancelled_bookings = all_bookings.filter(status='cancelled')
    
    # Airport codes dictionary
    airport_codes = {
        'Delhi': 'DEL',
        'Mumbai': 'BOM',
        'Bangalore': 'BLR',
        'Chennai': 'MAA',
        'Kolkata': 'CCU',
        'Hyderabad': 'HYD',
        'Pune': 'PNQ',
        'Ahmedabad': 'AMD',
        'Jaipur': 'JAI',
        'Goa': 'GOI',
        'Kochi': 'COK',
        'Thiruvananthapuram': 'TRV',
        'Lucknow': 'LKO',
        'Guwahati': 'GAU',
        'New York': 'JFK',
        'London': 'LHR',
        'Dubai': 'DXB',
        'Singapore': 'SIN',
        'Bangkok': 'BKK',
        'Paris': 'CDG',
        'Tokyo': 'NRT',
        'Sydney': 'SYD',
        'Toronto': 'YYZ',
        'Frankfurt': 'FRA',
        'Amsterdam': 'AMS',
        'Zurich': 'ZRH',
        'Vienna': 'VIE',
        'Brussels': 'BRU',
        'Copenhagen': 'CPH',
        'Stockholm': 'ARN',
        'Oslo': 'OSL',
        'Helsinki': 'HEL',
        'Dublin': 'DUB',
        'Madrid': 'MAD',
        'Barcelona': 'BCN',
        'Rome': 'FCO',
        'Milan': 'MXP',
        'Munich': 'MUC',
        'Berlin': 'TXL',
        'Prague': 'PRG',
        'Warsaw': 'WAW',
        'Budapest': 'BUD',
        'Athens': 'ATH',
        'Istanbul': 'IST',
        'Cairo': 'CAI',
        'Tel Aviv': 'TLV',
        'Doha': 'DOH',
        'Kuwait': 'KWI',
        'Riyadh': 'RUH',
        'Jeddah': 'JED',
        'Muscat': 'MCT',
        'Colombo': 'CMB',
        'Male': 'MLE',
        'Kathmandu': 'KTM',
        'Dhaka': 'DAC',
        'Karachi': 'KHI',
        'Lahore': 'LHE',
        'Islamabad': 'ISB',
        'Kuala Lumpur': 'KUL',
        'Jakarta': 'CGK',
        'Manila': 'MNL',
        'Ho Chi Minh': 'SGN',
        'Hanoi': 'HAN',
        'Hong Kong': 'HKG',
        'Seoul': 'ICN',
        'Busan': 'PUS',
        'Melbourne': 'MEL',
        'Perth': 'PER',
        'Brisbane': 'BNE',
        'Auckland': 'AKL',
        'Christchurch': 'CHC'
    }
    
    context = {
        'total_bookings': all_bookings.count(),
        'upcoming_count': upcoming_bookings.count(),
        'completed_count': past_bookings.count(),
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'cancelled_bookings': cancelled_bookings,
        'airport_codes': airport_codes,
    }
    return render(request, 'dashboard_new.html', context)


@login_required
def cancel_booking(request, booking_id):
    """Cancel a booking"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status == 'confirmed':
        # Return seats to schedule
        schedule = booking.schedule
        schedule.available_seats += booking.seats_booked
        schedule.save()
        
        # Update booking status
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, 'Your booking has been cancelled.')
    else:
        messages.error(request, 'This booking cannot be cancelled.')
    
    return redirect('dashboard')


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
                messages.success(request, f'Welcome back, {user.profile.full_name}!')
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

@require_http_methods(['GET', 'POST'])
def user_signup(request):
    """Handle new user registration"""
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
            # Collect all form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = UserRegisterForm()
    
    return render(request, 'signup.html', {'form': form})
    return render(request, 'signup.html', {'form': form})


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
    
    # Airport codes dictionary for display
    airport_codes = {
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
        'Dubai': 'DXB',
        'Singapore': 'SIN',
        'Bangkok': 'BKK',
        'London': 'LHR',
        'New York': 'JFK',
        'Paris': 'CDG',
        'Tokyo': 'NRT',
        'Sydney': 'SYD',
    }
    
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


@login_required
@user_passes_test(is_staff_user)
def delete_package(request, package_id):
    """Delete package"""
    if request.method == 'POST':
        package = get_object_or_404(Package, id=package_id)
        package.delete()
        messages.success(request, 'Package deleted successfully!')
    
    return redirect('admin_packages')
