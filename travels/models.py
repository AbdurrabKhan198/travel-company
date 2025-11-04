from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Route(models.Model):
    """Flight routes available in the system"""
    from_location = models.CharField(max_length=100)
    to_location = models.CharField(max_length=100)
    duration = models.CharField(max_length=50, help_text="e.g., 2h 30m")
    flight_number = models.CharField(max_length=20, unique=True)
    ROUTE_TYPE_CHOICES = [
        ('domestic', 'Domestic'),
        ('international', 'International'),
    ]
    route_type = models.CharField(max_length=20, choices=ROUTE_TYPE_CHOICES, default='domestic')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['from_location', 'to_location', 'flight_number']
    
    def __str__(self):
        return f"{self.flight_number}: {self.from_location} → {self.to_location}"

class Inventory(models.Model):
    """Available tickets inventory managed by admin"""
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='inventory')
    travel_date = models.DateField()
    total_seats = models.IntegerField(default=180)
    available_seats = models.IntegerField(default=180)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['route', 'travel_date']
        ordering = ['travel_date']
    
    def __str__(self):
        return f"{self.route.flight_number} - {self.travel_date} ({self.available_seats} seats)"
    
    @property
    def is_available(self):
        return self.is_active and self.available_seats > 0 and self.travel_date >= timezone.now().date()

class Booking(models.Model):
    """User bookings"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    ID_TYPE_CHOICES = [
        ('aadhar', 'Aadhar Card'),
        ('passport', 'Passport'),
        ('voter', 'Voter ID'),
        ('driving', 'Driving License'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='bookings')
    booking_reference = models.CharField(max_length=20, unique=True)
    
    # Passenger details
    passenger_name = models.CharField(max_length=200)
    passenger_age = models.IntegerField()
    passenger_gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    id_type = models.CharField(max_length=20, choices=ID_TYPE_CHOICES)
    id_last_4_digits = models.CharField(max_length=4)
    
    # Booking details
    seats_booked = models.IntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    
    # Timestamps
    booked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-booked_at']
    
    def __str__(self):
        return f"{self.booking_reference} - {self.user.username} - {self.inventory.route.flight_number}"
    
    @property
    def is_upcoming(self):
        return self.inventory.travel_date >= timezone.now().date() and self.status == 'confirmed'

class Package(models.Model):
    """Travel packages featured on homepage"""
    destination = models.CharField(max_length=200)
    title = models.CharField(max_length=300)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.CharField(max_length=50, help_text="e.g., 5 Days 4 Nights")
    image_url = models.URLField(blank=True, null=True)
    is_featured = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return f"{self.destination} - {self.title}"
