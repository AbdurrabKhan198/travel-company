from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, date
import random
import string

from .models import Route, Inventory, Booking, Package


def homepage(request):
    """Homepage with search and featured packages"""
    packages = Package.objects.filter(is_featured=True)[:6]
    
    # Get unique locations for search dropdowns
    origins = Route.objects.values_list('from_location', flat=True).distinct()
    destinations = Route.objects.values_list('to_location', flat=True).distinct()
    
    context = {
        'packages': packages,
        'origins': origins,
        'destinations': destinations,
        'today': date.today().isoformat(),
    }
    return render(request, 'index.html', context)


def search_flights(request):
    """Search for available flights"""
    from_location = request.GET.get('from_location', '')
    to_location = request.GET.get('to_location', '')
    travel_date = request.GET.get('travel_date', '')
    route_type = request.GET.get('route_type', '').strip()
    
    flights = Inventory.objects.select_related('route').filter(
        route__from_location=from_location,
        route__to_location=to_location,
        is_active=True
    )
    if route_type and route_type in dict(Route.ROUTE_TYPE_CHOICES):
        flights = flights.filter(route__route_type=route_type)
    
    if travel_date:
        try:
            travel_date_obj = datetime.strptime(travel_date, '%Y-%m-%d').date()
            flights = flights.filter(travel_date=travel_date_obj)
        except ValueError:
            pass
    
    # Filter only future dates
    flights = flights.filter(travel_date__gte=timezone.now().date())
    
    context = {
        'flights': flights,
        'from_location': from_location,
        'to_location': to_location,
        'travel_date': travel_date,
        'route_type': route_type,
    }
    return render(request, 'search.html', context)


@login_required
def booking_page(request, inventory_id):
    """Booking page for a specific flight"""
    inventory = get_object_or_404(Inventory, id=inventory_id)
    
    if request.method == 'POST':
        # Process booking
        passenger_name = request.POST.get('passenger_name')
        passenger_age = request.POST.get('passenger_age')
        passenger_gender = request.POST.get('passenger_gender')
        id_type = request.POST.get('id_type')
        id_last_4_digits = request.POST.get('id_last_4_digits')
        seats_booked = int(request.POST.get('seats_booked', 1))
        
        # Check availability
        if inventory.available_seats < seats_booked:
            messages.error(request, 'Not enough seats available!')
            return redirect('booking', inventory_id=inventory_id)
        
        # Generate booking reference
        booking_ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        # Calculate total amount
        total_amount = inventory.price * seats_booked
        
        # Create booking
        booking = Booking.objects.create(
            user=request.user,
            inventory=inventory,
            booking_reference=booking_ref,
            passenger_name=passenger_name,
            passenger_age=passenger_age,
            passenger_gender=passenger_gender,
            id_type=id_type,
            id_last_4_digits=id_last_4_digits,
            seats_booked=seats_booked,
            total_amount=total_amount,
            status='confirmed'
        )
        
        # Update inventory
        inventory.available_seats -= seats_booked
        inventory.save()
        
        messages.success(request, f'Booking confirmed! Reference: {booking_ref}')
        return redirect('dashboard')
    
    context = {
        'inventory': inventory,
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
    all_bookings = Booking.objects.filter(user=request.user).select_related('inventory__route')
    
    upcoming_bookings = all_bookings.filter(
        inventory__travel_date__gte=today,
        status='confirmed'
    )
    
    past_bookings = all_bookings.filter(
        inventory__travel_date__lt=today,
        status='confirmed'
    )
    
    cancelled_bookings = all_bookings.filter(status='cancelled')
    
    context = {
        'total_bookings': all_bookings.count(),
        'upcoming_count': upcoming_bookings.count(),
        'completed_count': past_bookings.count(),
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'cancelled_bookings': cancelled_bookings,
    }
    return render(request, 'dashboard.html', context)


@login_required
def cancel_booking(request, booking_id):
    """Cancel a booking"""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status == 'confirmed':
        # Return seats to inventory
        inventory = booking.inventory
        inventory.available_seats += booking.seats_booked
        inventory.save()
        
        # Update booking status
        booking.status = 'cancelled'
        booking.save()
        
        messages.success(request, 'Booking cancelled successfully!')
    else:
        messages.error(request, 'This booking cannot be cancelled.')
    
    return redirect('dashboard')


def user_login(request):
    """Login view"""
    if request.user.is_authenticated:
        return redirect('homepage')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('homepage')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'login.html')


def user_signup(request):
    """Signup view"""
    if request.user.is_authenticated:
        return redirect('homepage')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match!')
            return redirect('signup')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return redirect('signup')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return redirect('signup')
        
        # Create user
        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)
        messages.success(request, 'Account created successfully!')
        return redirect('homepage')
    
    return render(request, 'signup.html')


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
def admin_inventory(request):
    """Admin inventory management"""
    inventory_list = Inventory.objects.select_related('route').all().order_by('-travel_date')
    routes = Route.objects.all()
    
    # Stats
    total_routes = Route.objects.count()
    active_inventory = Inventory.objects.filter(is_active=True).count()
    total_seats = Inventory.objects.aggregate(Sum('available_seats'))['available_seats__sum'] or 0
    today_bookings = Booking.objects.filter(booked_at__date=timezone.now().date()).count()
    
    context = {
        'inventory_list': inventory_list,
        'routes': routes,
        'total_routes': total_routes,
        'active_inventory': active_inventory,
        'total_seats': total_seats,
        'today_bookings': today_bookings,
    }
    return render(request, 'admin_inventory.html', context)


@login_required
@user_passes_test(is_staff_user)
def add_inventory(request):
    """Add new inventory"""
    if request.method == 'POST':
        route_id = request.POST.get('route')
        travel_date = request.POST.get('travel_date')
        price = request.POST.get('price')
        total_seats = request.POST.get('total_seats', 180)
        is_active = request.POST.get('is_active') == 'true'
        
        route = get_object_or_404(Route, id=route_id)
        
        # Check if inventory already exists
        if Inventory.objects.filter(route=route, travel_date=travel_date).exists():
            messages.error(request, 'Inventory for this route and date already exists!')
        else:
            Inventory.objects.create(
                route=route,
                travel_date=travel_date,
                total_seats=total_seats,
                available_seats=total_seats,
                price=price,
                is_active=is_active
            )
            messages.success(request, 'Inventory added successfully!')
    
    return redirect('admin_inventory')


@login_required
@user_passes_test(is_staff_user)
def delete_inventory(request, inventory_id):
    """Delete inventory"""
    if request.method == 'POST':
        inventory = get_object_or_404(Inventory, id=inventory_id)
        inventory.delete()
        messages.success(request, 'Inventory deleted successfully!')
    
    return redirect('admin_inventory')


@login_required
@user_passes_test(is_staff_user)
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
