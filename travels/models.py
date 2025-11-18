from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.core.validators import MinLengthValidator, RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid

class TimestampedModel(models.Model):
    """Abstract base class with created and updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class UserManager(BaseUserManager):
    """Custom user model manager where email is the unique identifier"""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Custom user model that uses email as the unique identifier"""
    class UserType(models.TextChoices):
        CUSTOMER = 'customer', _('Customer')
        STAFF = 'staff', _('Staff')
        ADMIN = 'admin', _('Admin')
    
    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone = models.CharField(_('phone number'), validators=[phone_regex], max_length=17, blank=True)
    user_type = models.CharField(_('user type'), max_length=20, choices=UserType.choices, default=UserType.CUSTOMER)
    is_verified = models.BooleanField(_('verified'), default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        permissions = [
            ('can_manage_bookings', 'Can manage bookings'),
            ('can_manage_routes', 'Can manage routes'),
            ('can_view_reports', 'Can view reports'),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def is_customer(self):
        return self.user_type == self.UserType.CUSTOMER
    
    @property
    def is_staff_member(self):
        return self.user_type in [self.UserType.STAFF, self.UserType.ADMIN]
    
    def save(self, *args, **kwargs):
        if not self.pk and not self.user_type:
            self.user_type = self.UserType.CUSTOMER
        super().save(*args, **kwargs)

class UserProfile(TimestampedModel):
    """Extended user profile with additional information"""
    GENDER_CHOICES = [
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
        ('P', _('Prefer not to say')),
    ]
    
    ID_TYPE_CHOICES = [
        ('aadhar', _('Aadhar Card')),
        ('passport', _('Passport')),
        ('voter', _('Voter ID')),
        ('driving', _('Driving License')),
        ('other', _('Other')),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(_('full name'), max_length=100)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    gender = models.CharField(_('gender'), max_length=1, choices=GENDER_CHOICES, blank=True)
    address = models.TextField(_('address'), blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True)
    state = models.CharField(_('state/province'), max_length=100, blank=True)
    country = models.CharField(_('country'), max_length=100, default='India')
    pincode = models.CharField(_('postal code'), max_length=10, blank=True)
    profile_picture = models.ImageField(
        _('profile picture'), 
        upload_to='profile_pics/', 
        blank=True, 
        null=True,
        help_text=_('Upload a profile picture (optional)')
    )
    id_type = models.CharField(
        _('ID type'), 
        max_length=20, 
        choices=ID_TYPE_CHOICES, 
        blank=True,
        help_text=_('Type of government-issued ID')
    )
    id_number = models.CharField(
        _('ID number'), 
        max_length=50, 
        blank=True,
        help_text=_('ID number of the selected ID type')
    )
    aadhar_number = models.CharField(
        _('Aadhar Number'),
        max_length=12,
        unique=True,
        null=True,
        blank=True,
        validators=[MinLengthValidator(12)],
        help_text=_('12-digit Aadhar number for security verification')
    )
    
    # PDF Documents
    id_document_pdf = models.FileField(
        _('ID Document PDF'),
        upload_to='user_documents/id/',
        blank=True,
        null=True,
        help_text=_('Upload your ID document (Aadhar, Passport, etc.) as PDF')
    )
    passport_pdf = models.FileField(
        _('Passport PDF'),
        upload_to='user_documents/passport/',
        blank=True,
        null=True,
        help_text=_('Upload your passport copy as PDF')
    )
    other_documents = models.FileField(
        _('Other Documents PDF'),
        upload_to='user_documents/other/',
        blank=True,
        null=True,
        help_text=_('Upload any other relevant documents as PDF')
    )
    
    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
    
    def __str__(self):
        return f"{self.full_name}'s profile"
    
    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    def clean(self):
        if self.date_of_birth and self.date_of_birth > date.today():
            raise ValidationError({'date_of_birth': _('Date of birth cannot be in the future')})
        if self.aadhar_number and not self.aadhar_number.isdigit():
            raise ValidationError({'aadhar_number': _('Aadhar number must contain only digits')})
        if self.aadhar_number and len(self.aadhar_number) != 12:
            raise ValidationError({'aadhar_number': _('Aadhar number must be exactly 12 digits')})

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create UserProfile when a User is created"""
    if created:
        # Create profile with default values
        try:
            UserProfile.objects.get_or_create(
                user=instance,
                defaults={
                    'full_name': instance.get_full_name() or instance.email.split('@')[0]
                }
            )
        except Exception as e:
            # Log error but don't fail user creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error creating user profile: {str(e)}')

class OTPVerification(models.Model):
    """Model to store OTP for email verification during signup"""
    email = models.EmailField(_('email address'), null=True, blank=True)
    aadhar_number = models.CharField(max_length=12, blank=True, null=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = _('OTP Verification')
        verbose_name_plural = _('OTP Verifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'is_verified'], name='otp_email_idx'),
        ]
    
    def __str__(self):
        return f"OTP for {self.email}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_expired() and not self.is_verified and self.attempts < 3
    
    def verify(self, entered_otp):
        """Verify the entered OTP"""
        if not self.is_valid():
            return False
        self.attempts += 1
        if self.otp == entered_otp:
            self.is_verified = True
            self.save()
            return True
        self.save()
        return False

class Route(TimestampedModel):
    """Travel routes available in the system"""
    ROUTE_TYPE_CHOICES = [
        ('domestic', _('Domestic')),
        ('international', _('International')),
    ]
    
    TRANSPORT_TYPE_CHOICES = [
        ('flight', _('Flight')),
        ('bus', _('Bus')),
        ('train', _('Train')),
        ('cruise', _('Cruise')),
    ]
    
    name = models.CharField(_('route name'), max_length=200, help_text=_('E.g., Mumbai to Delhi Express'))
    from_location = models.CharField(_('from'), max_length=100)
    to_location = models.CharField(_('to'), max_length=100)
    transport_type = models.CharField(_('transport type'), max_length=20, choices=TRANSPORT_TYPE_CHOICES, default='flight')
    carrier_number = models.CharField(_('flight/bus/train number'), max_length=20, unique=True)
    departure_time = models.TimeField(_('departure time'))
    arrival_time = models.TimeField(_('arrival time'))
    duration = models.DurationField(_('duration'), help_text=_('Format: HH:MM:SS'))
    route_type = models.CharField(_('route type'), max_length=20, choices=ROUTE_TYPE_CHOICES, default='domestic')
    base_price = models.DecimalField(_('base price'), max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(_('active'), default=True)
    description = models.TextField(_('description'), blank=True)
    amenities = models.JSONField(_('amenities'), default=dict, blank=True,
                               help_text=_('JSON of available amenities (e.g., {"wifi": true, "meals": true})'))
    departure_terminal = models.CharField(_('departure terminal'), max_length=20, 
                                         help_text=_('Terminal number/name for departure (e.g., T1, T2, Terminal A)'))
    arrival_terminal = models.CharField(_('arrival terminal'), max_length=20,
                                       help_text=_('Terminal number/name for arrival (e.g., T1, T2, Terminal A)'))
    is_non_refundable = models.BooleanField(_('non-refundable'), default=False,
                                           help_text=_('Mark this route as non-refundable'))
    
    class Meta:
        verbose_name = _('route')
        verbose_name_plural = _('routes')
        ordering = ['from_location', 'to_location', 'departure_time']
        unique_together = ['from_location', 'to_location', 'carrier_number', 'departure_time']
    
    def __str__(self):
        return f"{self.from_location} to {self.to_location} ({self.carrier_number})"
    
    def clean(self):
        if self.from_location == self.to_location:
            raise ValidationError(_('Origin and destination cannot be the same'))
        if self.departure_time and self.arrival_time and self.arrival_time <= self.departure_time:
            raise ValidationError(_('Arrival time must be after departure time'))
    
    @property
    def formatted_duration(self):
        """Return duration in a human-readable format"""
        total_seconds = int(self.duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m" if hours else f"{minutes}m"
    
    def calculate_arrival_date(self, departure_date):
        """Calculate arrival date based on departure date and duration"""
        if not departure_date:
            return None
        
        # Calculate arrival datetime
        departure_datetime = datetime.combine(departure_date, self.departure_time)
        arrival_datetime = departure_datetime + self.duration
        
        return arrival_datetime.date()
    
    def get_available_dates(self, start_date=None, end_date=None, min_seats=1):
        """Get all available dates for this route within a date range"""
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=60)
        
        schedules = self.schedules.filter(
            departure_date__gte=start_date,
            departure_date__lte=end_date,
            available_seats__gte=min_seats,
            is_active=True
        ).order_by('departure_date')
        
        return schedules
    
    def is_available_on_date(self, check_date, min_seats=1):
        """Check if route has available seats on a specific date"""
        return self.schedules.filter(
            departure_date=check_date,
            available_seats__gte=min_seats,
            is_active=True
        ).exists()

class Schedule(TimestampedModel):
    """Schedule for a specific route on specific dates"""
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='schedules')
    departure_date = models.DateField(_('departure date'))
    arrival_date = models.DateField(_('arrival date'))
    total_seats = models.PositiveIntegerField(_('total seats'), default=50)
    available_seats = models.PositiveIntegerField(_('available seats'), default=50)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(_('active'), default=True)
    notes = models.TextField(_('notes'), blank=True)
    
    class Meta:
        verbose_name = _('schedule')
        verbose_name_plural = _('schedules')
        ordering = ['departure_date', 'route__departure_time']
        unique_together = ['route', 'departure_date']
    
    def __str__(self):
        return f"{self.route} - {self.departure_date}"
    
    def clean(self):
        if self.arrival_date < self.departure_date:
            raise ValidationError(_('Arrival date cannot be before departure date'))
        if self.available_seats > self.total_seats:
            raise ValidationError(_('Available seats cannot exceed total seats'))
    
    @property
    def is_available(self):
        """Check if there are available seats and the schedule is active"""
        return self.available_seats > 0 and self.is_active
    
    def book_seats(self, seats=1):
        """Book specified number of seats"""
        if not self.is_available or seats > self.available_seats:
            return False
        self.available_seats -= seats
        self.save()
        return True
    
    def cancel_booking(self, seats=1):
        """Cancel booking and release seats"""
        if (self.available_seats + seats) > self.total_seats:
            return False
        self.available_seats += seats
        self.save()
        return True
    
    @property
    def departure_datetime(self):
        """Get full departure datetime combining date and time"""
        if self.departure_date and self.route.departure_time:
            return datetime.combine(self.departure_date, self.route.departure_time)
        return None
    
    @property
    def arrival_datetime(self):
        """Get full arrival datetime combining date and time"""
        if self.arrival_date and self.route.arrival_time:
            return datetime.combine(self.arrival_date, self.route.arrival_time)
        return None
    
    @property
    def is_past(self):
        """Check if this schedule is in the past"""
        if not self.departure_date:
            return False
        return self.departure_date < date.today()
    
    @property
    def is_today(self):
        """Check if this schedule is today"""
        if not self.departure_date:
            return False
        return self.departure_date == date.today()
    
    @property
    def days_until_departure(self):
        """Get number of days until departure"""
        if not self.departure_date:
            return None
        delta = self.departure_date - date.today()
        return delta.days
    
    def get_price_for_passengers(self, num_passengers=1):
        """Calculate total price for multiple passengers"""
        return self.price * Decimal(str(num_passengers))
    
    def can_book(self, num_seats=1):
        """Check if specified number of seats can be booked"""
        return self.is_available and self.available_seats >= num_seats

class Booking(TimestampedModel):
    """User travel bookings"""
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        CANCELLED = 'cancelled', _('Cancelled')
        COMPLETED = 'completed', _('Completed')
        NO_SHOW = 'no_show', _('No Show')
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PAID = 'paid', _('Paid')
        FAILED = 'failed', _('Failed')
        REFUNDED = 'refunded', _('Refunded')
        PARTIALLY_REFUNDED = 'partially_refunded', _('Partially Refunded')
    
    # Booking details
    booking_reference = models.CharField(_('booking reference'), max_length=12, unique=True, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='bookings',
        verbose_name=_('user')
    )
    schedule = models.ForeignKey(
        Schedule, 
        on_delete=models.PROTECT, 
        related_name='bookings',
        verbose_name=_('schedule')
    )
    
    # Passenger information
    contact_email = models.EmailField(_('contact email'))
    contact_phone = models.CharField(_('contact phone'), max_length=20)
    
    # Booking status
    status = models.CharField(
        _('status'), 
        max_length=20, 
        choices=Status.choices, 
        default=Status.PENDING
    )
    payment_status = models.CharField(
        _('payment status'), 
        max_length=20, 
        choices=PaymentStatus.choices, 
        default=PaymentStatus.PENDING
    )
    
    # Financial information
    base_fare = models.DecimalField(_('base fare'), max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(_('tax amount'), max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(_('discount amount'), max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(_('total amount'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('currency'), max_length=3, default='INR')
    
    # Additional information
    special_requests = models.TextField(_('special requests'), blank=True)
    notes = models.TextField(_('internal notes'), blank=True, help_text=_('Internal notes not visible to the customer'))
    
    # Audit fields
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    
    class Meta:
        verbose_name = _('booking')
        verbose_name_plural = _('bookings')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_reference'], name='booking_ref_idx'),
            models.Index(fields=['status'], name='booking_status_idx'),
            models.Index(fields=['payment_status'], name='booking_payment_status_idx'),
        ]
    
    def __str__(self):
        return f"{self.booking_reference} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        if not self.total_amount:
            self.calculate_total()
        super().save(*args, **kwargs)
    
    def generate_booking_reference(self):
        """Generate a unique booking reference"""
        import random
        import string
        
        while True:
            # Format: SB + 6 random alphanumeric characters (uppercase)
            ref = 'SB' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Booking.objects.filter(booking_reference=ref).exists():
                return ref
    
    def calculate_total(self):
        """Calculate the total amount including taxes and discounts"""
        self.total_amount = (self.base_fare + self.tax_amount - self.discount_amount).quantize(Decimal('0.01'))
    
    def calculate_for_passengers(self, num_passengers=1):
        """Calculate booking amounts for multiple passengers"""
        if not self.schedule:
            return
        
        # Base fare per passenger
        fare_per_passenger = self.schedule.price
        self.base_fare = fare_per_passenger * Decimal(str(num_passengers))
        
        # Calculate tax (typically 5-18% of base fare)
        tax_rate = Decimal('0.12')  # 12% GST
        self.tax_amount = (self.base_fare * tax_rate).quantize(Decimal('0.01'))
        
        # Apply discount if any (can be customized)
        self.discount_amount = Decimal('0.00')
        
        # Calculate total
        self.calculate_total()
    
    @property
    def is_upcoming(self):
        """Check if the booking is for a future date"""
        return self.schedule.departure_date >= date.today() and self.status == self.Status.CONFIRMED
    
    def cancel(self, refund_amount=None):
        """Cancel the booking and update inventory"""
        if self.status == self.Status.CANCELLED:
            return False
            
        self.status = self.Status.CANCELLED
        if refund_amount is not None:
            if refund_amount < self.total_amount:
                self.payment_status = self.PaymentStatus.PARTIALLY_REFUNDED
            else:
                self.payment_status = self.PaymentStatus.REFUNDED
        
        # Release the seats back to inventory (number of passengers)
        num_passengers = self.passengers.count() or 1
        self.schedule.cancel_booking(seats=num_passengers)
        self.save()
        return True
    
    def confirm(self):
        """Confirm the booking"""
        if self.status != self.Status.PENDING:
            return False
        
        # Get number of passengers
        num_passengers = self.passengers.count() or 1
            
        # Attempt to book the seats
        if not self.schedule.book_seats(seats=num_passengers):
            return False
            
        self.status = self.Status.CONFIRMED
        self.payment_status = self.PaymentStatus.PAID
        self.save()
        return True
    
    @property
    def num_passengers(self):
        """Get number of passengers in this booking"""
        return self.passengers.count()
    
    @property
    def flight_info(self):
        """Get formatted flight information"""
        if not self.schedule:
            return "N/A"
        route = self.schedule.route
        return f"{route.carrier_number} - {route.from_location} to {route.to_location}"
    
    @property
    def ticket_date(self):
        """Get the ticket/booking date"""
        return self.created_at.date() if self.created_at else None
    
    @property
    def travel_date(self):
        """Get the travel/departure date"""
        return self.schedule.departure_date if self.schedule else None
    
    @property
    def is_upcoming_travel(self):
        """Check if travel is in the future"""
        if not self.travel_date:
            return False
        return self.travel_date >= date.today() and self.status == self.Status.CONFIRMED

class Package(TimestampedModel):
    """Travel packages featured on the platform"""
    class PackageType(models.TextChoices):
        VACATION = 'vacation', _('Vacation Package')
        HONEYMOON = 'honeymoon', _('Honeymoon Package')
        ADVENTURE = 'adventure', _('Adventure Package')
        CRUISE = 'cruise', _('Cruise Package')
        PILGRIMAGE = 'pilgrimage', _('Pilgrimage Package')
        CUSTOM = 'custom', _('Custom Package')
    
    title = models.CharField(_('package title'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    destination = models.CharField(_('destination'), max_length=200)
    short_description = models.TextField(_('short description'), max_length=200)
    description = models.TextField(_('detailed description'))
    duration_days = models.PositiveIntegerField(_('duration in days'))
    duration_nights = models.PositiveIntegerField(_('duration in nights'))
    base_price = models.DecimalField(_('starting price'), max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_percentage = models.DecimalField(_('discount percentage'), max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    package_type = models.CharField(_('package type'), max_length=20, choices=PackageType.choices, default=PackageType.VACATION)
    is_featured = models.BooleanField(_('featured'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    
    # Itinerary (stored as JSON for flexibility)
    itinerary = models.JSONField(_('itinerary'), default=list, blank=True,
                               help_text=_('List of daily activities in JSON format'))
    
    # Inclusions and exclusions
    inclusions = models.JSONField(_('inclusions'), default=list, blank=True,
                                help_text=_('List of what\'s included in the package'))
    exclusions = models.JSONField(_('exclusions'), default=list, blank=True,
                                 help_text=_('List of what\'s not included in the package'))
    
    # Images
    main_image = models.ImageField(_('main image'), upload_to='packages/main/')
    gallery = models.ManyToManyField('PackageImage', blank=True, related_name='package_gallery')
    
    # SEO fields
    meta_title = models.CharField(_('meta title'), max_length=100, blank=True)
    meta_description = models.TextField(_('meta description'), blank=True)
    meta_keywords = models.TextField(_('meta keywords'), blank=True)
    
    class Meta:
        verbose_name = _('travel package')
        verbose_name_plural = _('travel packages')
        ordering = ['-is_featured', 'title']
        indexes = [
            models.Index(fields=['slug'], name='package_slug_idx'),
            models.Index(fields=['is_featured'], name='package_featured_idx'),
            models.Index(fields=['package_type'], name='package_type_idx'),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.destination}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.title} {self.destination}")
        if not self.meta_title:
            self.meta_title = f"{self.title} - {self.destination} | Safar Zone Travels"
        if not self.meta_description:
            self.meta_description = self.short_description[:160]  # Truncate to 120 chars for SEO
        super().save(*args, **kwargs)
    
    @property
    def discounted_price(self):
        """Calculate price after applying discount"""
        if self.discount_percentage > 0:
            return self.base_price * (1 - self.discount_percentage / 100)
        return self.base_price
    
    @property
    def duration_display(self):
        """Return formatted duration string"""
        return f"{self.duration_days} Days / {self.duration_nights} Nights"
    
    def get_absolute_url(self):
        """Get canonical URL for the package"""
        from django.urls import reverse
        return reverse('package_detail', kwargs={'slug': self.slug})

class PackageImage(models.Model):
    """Images for travel packages"""
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(_('image'), upload_to='packages/gallery/')
    caption = models.CharField(_('caption'), max_length=200, blank=True)
    is_primary = models.BooleanField(_('primary image'), default=False)
    display_order = models.PositiveIntegerField(_('display order'), default=0)
    
    class Meta:
        verbose_name = _('package image')
        verbose_name_plural = _('package images')
        ordering = ['display_order', 'id']
    
    def __str__(self):
        return f"Image for {self.package.title}"
    
    def save(self, *args, **kwargs):
        # If this is set as primary, unset any existing primary for this package
        if self.is_primary:
            PackageImage.objects.filter(package=self.package, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

class BookingPassenger(models.Model):
    """Passenger details for a booking"""
    class PassengerType(models.TextChoices):
        ADULT = 'adult', _('Adult (12+ years)')
        CHILD = 'child', _('Child (2-11 years)')
        INFANT = 'infant', _('Infant (0-2 years)')
        SENIOR = 'senior', _('Senior Citizen (60+ years)')
    
    class Title(models.TextChoices):
        MR = 'Mr', _('Mr')
        MRS = 'Mrs', _('Mrs')
        MISS = 'Miss', _('Miss')
        MASTER = 'Master', _('Master')
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='passengers')
    title = models.CharField(_('title'), max_length=10, choices=Title.choices, default=Title.MR)
    first_name = models.CharField(_('first name'), max_length=100)
    last_name = models.CharField(_('last name'), max_length=100)
    date_of_birth = models.DateField(_('date of birth'))
    gender = models.CharField(_('gender'), max_length=1, choices=UserProfile.GENDER_CHOICES)
    passport_number = models.CharField(_('passport number'), max_length=20, blank=True)
    passport_expiry = models.DateField(_('passport expiry'), null=True, blank=True)
    nationality = models.CharField(_('nationality'), max_length=100, default='Indian')
    passenger_type = models.CharField(
        _('passenger type'), 
        max_length=10, 
        choices=PassengerType.choices, 
        default=PassengerType.ADULT
    )
    special_requests = models.TextField(_('special requests'), blank=True)
    seat_preference = models.CharField(_('seat preference'), max_length=20, blank=True)
    
    class Meta:
        verbose_name = _('passenger')
        verbose_name_plural = _('passengers')
    
    def __str__(self):
        return f"{self.get_title_display()} {self.first_name} {self.last_name} ({self.get_passenger_type_display()})"
    
    @property
    def full_name(self):
        return f"{self.get_title_display()} {self.first_name} {self.last_name}"
    
    @property
    def full_name_with_title(self):
        """Return full name with title prefix"""
        return f"{self.get_title_display()} {self.first_name} {self.last_name}"
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    @property
    def is_passport_valid(self):
        """Check if passport is valid (not expired)"""
        if not self.passport_expiry:
            return True  # If no expiry date, assume valid
        return self.passport_expiry > date.today()
    
    @property
    def passport_expires_soon(self):
        """Check if passport expires within 6 months"""
        if not self.passport_expiry:
            return False
        six_months_later = date.today() + timedelta(days=180)
        return self.passport_expiry <= six_months_later
    
    def clean(self):
        """Validate passenger data"""
        errors = {}
        
        # Check passport expiry
        if self.passport_expiry and self.passport_expiry < date.today():
            errors['passport_expiry'] = _('Passport has expired')
        
        # Check date of birth
        if self.date_of_birth and self.date_of_birth > date.today():
            errors['date_of_birth'] = _('Date of birth cannot be in the future')
        
        if errors:
            raise ValidationError(errors)

class Contact(TimestampedModel):
    """Contact form submissions"""
    class Status(models.TextChoices):
        NEW = 'new', _('New')
        READ = 'read', _('Read')
        REPLIED = 'replied', _('Replied')
        CLOSED = 'closed', _('Closed')
    
    name = models.CharField(_('name'), max_length=100)
    email = models.EmailField(_('email address'))
    phone = models.CharField(_('phone number'), max_length=20, blank=True)
    subject = models.CharField(_('subject'), max_length=200, blank=True)
    message = models.TextField(_('message'))
    status = models.CharField(
        _('status'), 
        max_length=20, 
        choices=Status.choices, 
        default=Status.NEW
    )
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    admin_notes = models.TextField(_('admin notes'), blank=True, help_text=_('Internal notes for admin'))
    
    class Meta:
        verbose_name = _('contact inquiry')
        verbose_name_plural = _('contact inquiries')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status'], name='contact_status_idx'),
            models.Index(fields=['email'], name='contact_email_idx'),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.email} ({self.get_status_display()})"
    
    @property
    def is_new(self):
        """Check if inquiry is new"""
        return self.status == self.Status.NEW
    
    @property
    def is_read(self):
        """Check if inquiry has been read"""
        return self.status in [self.Status.READ, self.Status.REPLIED, self.Status.CLOSED]

class Wallet(TimestampedModel):
    """Wallet for OD (Organizational Discount) users - Admin controlled access"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(_('balance'), max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(_('active'), default=False, help_text=_('Only admin can enable/disable wallet access'))
    max_balance = models.DecimalField(_('maximum balance'), max_digits=10, decimal_places=2, default=100000, validators=[MinValueValidator(0)], help_text=_('Maximum balance limit'))
    
    class Meta:
        verbose_name = _('wallet')
        verbose_name_plural = _('wallets')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Wallet - {self.user.email} (₹{self.balance})"
    
    def can_use(self):
        """Check if wallet can be used (active and has balance)"""
        return self.is_active and self.balance > 0
    
    def add_balance(self, amount, transaction_type='recharge', description='', reference_id=None):
        """Add balance to wallet and create transaction record"""
        if amount <= 0:
            raise ValidationError(_('Amount must be greater than zero'))
        
        if (self.balance + amount) > self.max_balance:
            raise ValidationError(_(f'Balance cannot exceed maximum limit of ₹{self.max_balance}'))
        
        self.balance += amount
        self.save()
        
        # Create transaction record
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=self.balance,
            description=description,
            reference_id=reference_id
        )
        
        return self.balance
    
    def deduct_balance(self, amount, transaction_type='payment', description='', reference_id=None):
        """Deduct balance from wallet and create transaction record"""
        if amount <= 0:
            raise ValidationError(_('Amount must be greater than zero'))
        
        if amount > self.balance:
            raise ValidationError(_('Insufficient wallet balance'))
        
        if not self.is_active:
            raise ValidationError(_('Wallet is not active'))
        
        self.balance -= amount
        self.save()
        
        # Create transaction record (negative amount for deduction)
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type=transaction_type,
            amount=-amount,
            balance_after=self.balance,
            description=description,
            reference_id=reference_id
        )
        
        return self.balance

class WalletTransaction(TimestampedModel):
    """Transaction history for wallet"""
    class TransactionType(models.TextChoices):
        RECHARGE = 'recharge', _('Recharge')
        PAYMENT = 'payment', _('Payment')
        REFUND = 'refund', _('Refund')
        ADJUSTMENT = 'adjustment', _('Admin Adjustment')
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(_('transaction type'), max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2, help_text=_('Positive for credit, negative for debit'))
    balance_after = models.DecimalField(_('balance after'), max_digits=10, decimal_places=2)
    description = models.TextField(_('description'), blank=True)
    reference_id = models.CharField(_('reference ID'), max_length=100, blank=True, null=True, help_text=_('Booking reference, payment ID, etc.'))
    
    class Meta:
        verbose_name = _('wallet transaction')
        verbose_name_plural = _('wallet transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'created_at'], name='wallet_transaction_idx'),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - ₹{abs(self.amount)} - {self.wallet.user.email}"
    
    @property
    def is_credit(self):
        """Check if transaction is a credit (positive amount)"""
        return self.amount > 0
    
    @property
    def is_debit(self):
        """Check if transaction is a debit (negative amount)"""
        return self.amount < 0
