from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinLengthValidator, RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import datetime, date
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
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=100)
    aadhar_number = models.CharField(
        max_length=12,
        validators=[MinLengthValidator(12)],
        unique=True,
        help_text='12-digit Aadhar number'
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='India')
    pincode = models.CharField(max_length=10, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

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
            self.refund_amount = refund_amount
            if refund_amount < self.total_amount:
                self.payment_status = self.PaymentStatus.PARTIALLY_REFUNDED
            else:
                self.payment_status = self.PaymentStatus.REFUNDED
        
        # Release the seats back to inventory
        self.schedule.cancel_booking(seats=1)  # Assuming 1 seat per booking for simplicity
        self.save()
        return True
    
    def confirm(self):
        """Confirm the booking"""
        if self.status != self.Status.PENDING:
            return False
            
        # Attempt to book the seats
        if not self.schedule.book_seats(seats=1):  # Assuming 1 seat per booking for simplicity
            return False
            
        self.status = self.Status.CONFIRMED
        self.save()
        return True

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
            self.meta_description = self.short_description[:160]  # Truncate to 160 chars for SEO
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
        ADULT = 'adult', _('Adult')
        CHILD = 'child', _('Child (2-12 years)')
        INFANT = 'infant', _('Infant (0-2 years)')
        SENIOR = 'senior', _('Senior Citizen (60+ years)')
    
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='passengers')
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
        return f"{self.first_name} {self.last_name} ({self.get_passenger_type_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
