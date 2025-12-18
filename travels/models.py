from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.utils import timezone
from django.db.models.signals import post_save, pre_save
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
    """Custom user model for staff and admin only - uses email as the unique identifier"""
    class UserType(models.TextChoices):
        STAFF = 'staff', _('Staff')
        ADMIN = 'admin', _('Admin')
    
    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone = models.CharField(_('phone number'), validators=[phone_regex], max_length=17, blank=True)
    user_type = models.CharField(_('user type'), max_length=20, choices=UserType.choices, default=UserType.STAFF)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('Admin')
        verbose_name_plural = _('Admins')
        permissions = [
            ('can_manage_bookings', 'Can manage bookings'),
            ('can_manage_routes', 'Can manage routes'),
            ('can_view_reports', 'Can view reports'),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def is_staff_member(self):
        return self.user_type in [self.UserType.STAFF, self.UserType.ADMIN]

    @property
    def is_approved(self):
        """Check if user is approved (delegates to profile for customers)"""
        if self.is_superuser or self.is_staff_member:
            return True
        if hasattr(self, 'profile'):
            return self.profile.is_approved
        return False
    
    def save(self, *args, **kwargs):
        # Only staff and admin can be created through User model
        if not self.user_type:
            self.user_type = self.UserType.STAFF
        
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
    
    TITLE_CHOICES = [
        ('Mr', _('Mr')),
        ('Mrs', _('Mrs')),
        ('Miss', _('Miss')),
        ('Ms', _('Ms')),
        ('Dr', _('Dr')),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    title = models.CharField(_('title'), max_length=10, choices=TITLE_CHOICES, default='Mr')
    full_name = models.CharField(_('full name'), max_length=100)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    gender = models.CharField(_('gender'), max_length=1, choices=GENDER_CHOICES, blank=True)
    company_name = models.CharField(_('company name'), max_length=200, blank=True, help_text=_('Name of your company'))
    address = models.TextField(_('address'), blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True)
    state = models.CharField(_('state/province'), max_length=100, blank=True)
    country = models.CharField(_('country'), max_length=100, default='India')
    pincode = models.CharField(_('postal code'), max_length=10, blank=True)
    
    # Account Status Fields (moved from User model)
    is_verified = models.BooleanField(_('verified'), default=False)
    is_approved = models.BooleanField(_('approved'), default=False, help_text=_('Account approval status - user can login only after approval'))
    client_id = models.CharField(
        _('Agency ID'), 
        max_length=20, 
        unique=True, 
        editable=False,
        null=True,
        blank=True,
        help_text=_('Unique agency identifier assigned on registration')
    )
    sales_representative = models.ForeignKey(
        'SalesRepresentative',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_agencies',
        verbose_name=_('Sales Representative'),
        help_text=_('Assigned sales representative for this agency')
    )
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
    
    gst_number = models.CharField(
        _('GST Number'),
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        help_text=_('GST number (Optional)')
    )
    
    # Signup Document Uploads
    aadhar_card_front = models.ImageField(
        _('Aadhar Card Front'),
        upload_to='user_documents/aadhar/front/',
        blank=True,
        null=True,
        help_text=_('Upload front side of your Aadhar card (Required)')
    )
    aadhar_card_back = models.ImageField(
        _('Aadhar Card Back'),
        upload_to='user_documents/aadhar/back/',
        blank=True,
        null=True,
        help_text=_('Upload back side of your Aadhar card (Required)')
    )
    
    # Logo Upload (Optional)
    logo = models.ImageField(
        _('Logo'),
        upload_to='user_documents/logo/',
        blank=True,
        null=True,
        help_text=_('Upload your company/personal logo (Optional)')
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
        verbose_name = _('Agency')
        verbose_name_plural = _('Agencies')
        indexes = [
            models.Index(fields=['client_id'], name='userprofile_client_id_idx'),
        ]
    
    def __str__(self):
        return f"{self.full_name}'s profile"
    
    def generate_client_id(self):
        """Generate a unique random client ID based on company name"""
        import random
        import string
        
        # Get company name prefix (first 2 alphanumeric characters)
        company_name = self.company_name or ''
        prefix_agency = ''.join(c for c in company_name if c.isalnum())[:2].upper()
        
        # Pad with 'X' if less than 2 characters
        if len(prefix_agency) < 2:
            prefix_agency = (prefix_agency + 'XX')[:2]
        
        while True:
            # Format: SZ + CompanyPrefix + Random String (no hyphens)
            # Example: SZSA1A2B3C4D
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            client_id = f'SZ{prefix_agency}{random_part}'
            
            # Check if this ID already exists
            if not UserProfile.objects.filter(client_id=client_id).exists():
                return client_id
    
    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    def save(self, *args, **kwargs):
        # Generate client_id if it doesn't exist (for new profiles)
        if not self.client_id:
            self.client_id = self.generate_client_id()
        
        super().save(*args, **kwargs)
    
    def clean(self):
        if self.date_of_birth and self.date_of_birth > date.today():
            raise ValidationError({'date_of_birth': _('Date of birth cannot be in the future')})
        if self.gst_number:
            import re
            if len(self.gst_number) != 15:
                raise ValidationError({'gst_number': _('GST number must be 15 characters long')})
            if not re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', self.gst_number.upper()):
                raise ValidationError({'gst_number': _('Please enter a valid GST number format (e.g., 27ABCDE1234F1Z5)')})

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

@receiver(pre_save, sender=UserProfile)
def store_old_is_approved(sender, instance, **kwargs):
    """Store old is_approved value before save"""
    if instance.pk:
        try:
            old_instance = UserProfile.objects.get(pk=instance.pk)
            instance._old_is_approved = old_instance.is_approved
        except UserProfile.DoesNotExist:
            instance._old_is_approved = False
    else:
        instance._old_is_approved = False

@receiver(post_save, sender=UserProfile)
def send_approval_email(sender, instance, created, **kwargs):
    """Send approval email when agency is approved"""
    # Only send email if agency is approved and this is not a new profile creation
    if not created and instance.is_approved:
        # Check if is_approved was just changed to True
        was_approved = getattr(instance, '_old_is_approved', False)
        
        # Only send if agency was not approved before
        if not was_approved and instance.is_approved:
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                from django.template.loader import render_to_string
                from django.urls import reverse
                
                user_name = instance.full_name or instance.user.email.split('@')[0]
                user_email = instance.user.email
                
                # Get login URL
                try:
                    from django.contrib.sites.models import Site
                    current_site = Site.objects.get_current()
                    login_url = f"https://{current_site.domain}{reverse('login')}"
                except:
                    login_url = f"https://safarzonetravels.com{reverse('login')}"
                
                subject = 'Account Approved - Safar Zone Travels'
                
                # Plain text fallback
                plain_message = f'''
Hello {user_name},

Your account has been successfully approved!

You can now use all services of Safar Zone Travels:
- Flight Booking
- Hotel Booking
- Package Booking
- And much more...

You can login with your email and password.

Thank you,
Safar Zone Travels Team
                '''
                
                # HTML email template with user details
                context = {
                    'user_name': user_name,
                    'user_email': user_email,
                    'login_url': login_url,
                }
                
                # Add agency ID if available
                if instance.client_id:
                    context['user_agency_id'] = instance.client_id
                
                html_message = render_to_string('emails/approval_email.html', context)
                
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@safarzonetravels.com')
                
                send_mail(
                    subject,
                    plain_message,
                    from_email,
                    [user_email],
                    fail_silently=False,
                    html_message=html_message,
                )
            except Exception as e:
                # Log error but don't fail the save
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Error sending approval email: {str(e)}')

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
    ]
    
    name = models.CharField(_('route name'), max_length=200, help_text=_('E.g., Mumbai to Delhi Express'))
    from_location = models.CharField(_('from'), max_length=100)
    to_location = models.CharField(_('to'), max_length=100)
    transport_type = models.CharField(_('transport type'), max_length=20, choices=TRANSPORT_TYPE_CHOICES, default='flight')
    airline_name = models.CharField(_('airline/flight company name'), max_length=100, blank=True, 
                                     help_text=_('E.g., Indigo, Air India, SpiceJet, Vistara, etc.'))
    carrier_number = models.CharField(_('flight number'), max_length=20, unique=True)
    departure_time = models.TimeField(_('departure time'))
    arrival_time = models.TimeField(_('arrival time'))
    duration = models.DurationField(_('duration'), help_text=_('Format: HH:MM:SS'))
    route_type = models.CharField(_('route type'), max_length=20, choices=ROUTE_TYPE_CHOICES, default='domestic')
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
    
    def get_airline_logo_url(self):
        """Get airline logo URL based on airline name from static files"""
        if not self.airline_name:
            return None
        
        from django.templatetags.static import static
        
        # Airline logo mapping - using static files from static/images/flight-logo/
        # Map airline names to their corresponding logo file names
        airline_logos = {
            'indigo': 'images/flight-logo/indigo.png',
            'indigo airlines': 'images/flight-logo/indigo.png',
            'indigo airline': 'images/flight-logo/indigo.png',
            'air arabia': 'images/flight-logo/air-arabia.png',
            'airarabia': 'images/flight-logo/air-arabia.png',
            'air india': 'images/flight-logo/air india.png',
            'airindia': 'images/flight-logo/air india.png',
            'air india express': 'images/flight-logo/air india.png',
            'flynas': 'images/flight-logo/flynas.png',
            'jazeera': 'images/flight-logo/jazeera.png',
            'jazeera airways': 'images/flight-logo/jazeera.png',
            'jazeera airway': 'images/flight-logo/jazeera.png',
            'saudi airlines': 'images/flight-logo/saudi-airline.png',
            'saudi arabian airlines': 'images/flight-logo/saudi-airline.png',
            'saudi arabia': 'images/flight-logo/saudi-airline.png',
            'saudi arabian': 'images/flight-logo/saudi-airline.png',
            'fly dubai': 'images/flight-logo/fly-dubai.png',
            'flydubai': 'images/flight-logo/fly-dubai.png',
            'fly dubai airlines': 'images/flight-logo/fly-dubai.png',
            'emirates': 'images/flight-logo/fly-dubai.png',  # Using fly-dubai as placeholder
            'emirates airlines': 'images/flight-logo/fly-dubai.png',
        }
        
        # Normalize airline name (lowercase, strip spaces)
        airline_key = self.airline_name.lower().strip()
        # Remove extra spaces
        airline_key = ' '.join(airline_key.split())
        
        # Try exact match first
        logo_path = airline_logos.get(airline_key)
        if logo_path:
            return static(logo_path)
        
        # Try partial match (contains check)
        for key, path in airline_logos.items():
            if key in airline_key or airline_key in key:
                return static(path)
        
        return None
    
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
    
    # Passenger-specific fares
    adult_fare = models.DecimalField(
        _('adult fare (12+ years)'), 
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        help_text=_('Fare for adults (12+ years)')
    )
    child_fare = models.DecimalField(
        _('child fare (2-11 years)'), 
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text=_('Fare for children (2-11 years). Typically around ₹4000. Child gets a seat.')
    )
    infant_fare = models.DecimalField(
        _('infant fare (0-2 years)'), 
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text=_('Fare for infants (0-2 years). Typically around ₹4000. Infant travels on mother\'s lap, no seat.')
    )
    
    # PNR - same for all passengers on this flight on this date
    pnr = models.CharField(
        _('PNR'), 
        max_length=10, 
        blank=True,
        db_index=True,
        help_text=_('Passenger Name Record - same for all passengers on this flight on this date')
    )
    
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
        """Calculate total price for multiple passengers (using adult fare)"""
        return self.adult_fare * Decimal(str(num_passengers))
    
    def get_fare_for_passenger_type(self, passenger_type):
        """
        Get fare for a specific passenger type.
        passenger_type: 'adult', 'child', or 'infant'
        Returns the appropriate fare.
        """
        if passenger_type == 'adult':
            return self.adult_fare
        elif passenger_type == 'child':
            return self.child_fare if self.child_fare is not None else self.adult_fare * Decimal('0.75')
        elif passenger_type == 'infant':
            return self.infant_fare if self.infant_fare is not None else self.adult_fare * Decimal('0.10')
        else:
            # Default to adult fare for unknown types
            return self.adult_fare
    
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
    
    # Return flight (for round trip bookings)
    return_schedule = models.ForeignKey(
        Schedule,
        on_delete=models.PROTECT,
        related_name='return_bookings',
        verbose_name=_('return schedule'),
        null=True,
        blank=True,
        help_text=_('Return flight schedule for round trip bookings')
    )
    
    # Trip type
    trip_type = models.CharField(
        _('trip type'),
        max_length=20,
        choices=[
            ('one_way', _('One Way')),
            ('return', _('Return')),
        ],
        default='one_way'
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
    
    # Coupon information
    coupon = models.ForeignKey(
        'Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
        verbose_name=_('coupon'),
        help_text=_('Applied coupon code')
    )
    
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
        
        # Base fare per passenger (using adult fare)
        fare_per_passenger = self.schedule.adult_fare
        self.base_fare = fare_per_passenger * Decimal(str(num_passengers))
        
        # Tax removed as per client request
        self.tax_amount = Decimal('0.00')
        
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

class Coupon(TimestampedModel):
    """Coupon codes for discounts on bookings"""
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', _('Percentage')
        FIXED = 'fixed', _('Fixed Amount')
    
    code = models.CharField(
        _('coupon code'),
        max_length=50,
        unique=True,
        help_text=_('Unique coupon code (e.g., SAVE20, FLAT500)')
    )
    discount_type = models.CharField(
        _('discount type'),
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE
    )
    discount_value = models.DecimalField(
        _('discount value'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Percentage (0-100) or fixed amount in INR')
    )
    min_purchase = models.DecimalField(
        _('minimum purchase'),
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Minimum booking amount required to use this coupon')
    )
    max_discount = models.DecimalField(
        _('maximum discount'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('Maximum discount amount (for percentage coupons). Leave blank for no limit.')
    )
    valid_from = models.DateTimeField(
        _('valid from'),
        help_text=_('Coupon valid from this date/time')
    )
    valid_to = models.DateTimeField(
        _('valid to'),
        help_text=_('Coupon valid until this date/time')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether this coupon is currently active')
    )
    usage_limit = models.PositiveIntegerField(
        _('usage limit'),
        null=True,
        blank=True,
        help_text=_('Maximum number of times this coupon can be used. Leave blank for unlimited.')
    )
    used_count = models.PositiveIntegerField(
        _('used count'),
        default=0,
        help_text=_('Number of times this coupon has been used')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Description of the coupon (visible to users)')
    )
    
    class Meta:
        verbose_name = _('coupon')
        verbose_name_plural = _('coupons')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code'], name='coupon_code_idx'),
            models.Index(fields=['is_active'], name='coupon_active_idx'),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.get_discount_type_display()}"
    
    def is_valid(self, user=None, booking_amount=None):
        """Check if coupon is valid for use"""
        now = timezone.now()
        
        # Check if active
        if not self.is_active:
            return False, "Coupon is not active"
        
        # Check date validity
        if now < self.valid_from:
            return False, f"Coupon is not yet valid. Valid from {self.valid_from.strftime('%d %b %Y')}"
        
        if now > self.valid_to:
            return False, f"Coupon has expired. Valid until {self.valid_to.strftime('%d %b %Y')}"
        
        # Check usage limit
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False, "Coupon usage limit reached"
        
        # Check minimum purchase
        if booking_amount and booking_amount < self.min_purchase:
            return False, f"Minimum purchase amount of ₹{self.min_purchase} required"
        
        return True, "Valid"
    
    def calculate_discount(self, booking_amount):
        """Calculate discount amount for given booking amount"""
        if self.discount_type == self.DiscountType.PERCENTAGE:
            discount = (booking_amount * self.discount_value) / Decimal('100')
            if self.max_discount:
                discount = min(discount, self.max_discount)
        else:  # FIXED
            discount = self.discount_value
        
        return discount.quantize(Decimal('0.01'))
    
    def apply_to_booking(self, booking):
        """Apply coupon to a booking and increment usage count"""
        if booking.coupon:
            return False, "Booking already has a coupon applied"
        
        is_valid, message = self.is_valid(booking_amount=booking.base_fare)
        if not is_valid:
            return False, message
        
        discount = self.calculate_discount(booking.base_fare)
        booking.coupon = self
        booking.discount_amount = discount
        booking.calculate_total()
        booking.save()
        
        # Increment usage count
        self.used_count += 1
        self.save()
        
        return True, f"Coupon applied successfully! Discount: ₹{discount}"

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
    pnr = models.CharField(
        _('PNR'), 
        max_length=10, 
        null=True,
        blank=True,
        editable=False,
        help_text=_('Passenger Name Record - same for all passengers on same flight and date')
    )
    
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

class ODWallet(TimestampedModel):
    """OD (Organizational Discount) Wallet - Admin controlled access and recharge only"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='od_wallet')
    balance = models.DecimalField(_('balance'), max_digits=10, decimal_places=2, default=0, help_text=_('Current balance (can be negative after expiry)'))
    is_active = models.BooleanField(_('active'), default=False, help_text=_('Only admin can enable/disable OD wallet access'))
    max_balance = models.DecimalField(_('maximum balance'), max_digits=10, decimal_places=2, default=100000, validators=[MinValueValidator(0)], help_text=_('Maximum balance limit'))
    expiry_days = models.IntegerField(_('expiry days'), default=0, help_text=_('Number of days after which wallet expires (0 = no expiry)'))
    expires_at = models.DateTimeField(_('expires at'), null=True, blank=True, help_text=_('Auto-calculated expiry date'))
    initial_balance = models.DecimalField(_('initial balance'), max_digits=10, decimal_places=2, default=0, help_text=_('Initial balance when wallet was created/activated'))
    
    class Meta:
        verbose_name = _('OD Wallet')
        verbose_name_plural = _('OD Wallets')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OD Wallet - {self.user.email} (₹{self.balance})"
    
    def save(self, *args, **kwargs):
        """Auto-calculate expires_at when expiry_days is set"""
        if self.expiry_days > 0 and not self.expires_at:
            from django.utils import timezone
            self.expires_at = timezone.now() + timedelta(days=self.expiry_days)
        elif self.expiry_days == 0:
            self.expires_at = None
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if wallet has expired"""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def days_remaining(self):
        """Calculate days remaining until expiry (returns negative if expired)"""
        if not self.expires_at:
            return None
        from django.utils import timezone
        now = timezone.now()
        delta = self.expires_at - now
        return delta.days  # Can be negative if expired
    
    def process_expiry(self):
        """Process expired wallet: deduct remaining balance and deactivate"""
        if not self.is_expired() or not self.is_active:
            return False
        
        # Calculate used amount (initial - current balance before expiry)
        # If balance is already negative, it means it was processed before
        if self.balance < 0:
            return False  # Already processed
        
        # Calculate how much was used
        used_amount = self.initial_balance - self.balance
        
        # Deduct remaining balance (make it negative to show used amount)
        remaining_balance = self.balance
        if remaining_balance > 0:
            # Set balance to negative of used amount
            self.balance = -used_amount
            self.is_active = False
            self.save()
            
            # Create transaction record for expiry deduction
            ODWalletTransaction.objects.create(
                od_wallet=self,
                transaction_type='adjustment',
                amount=-remaining_balance,
                balance_after=self.balance,
                description=f'Wallet expired. Remaining balance ₹{remaining_balance} deducted. Used: ₹{used_amount}',
                reference_id='EXPIRY_AUTO'
            )
            return True
        elif remaining_balance == 0:
            # Balance is zero, just deactivate
            self.is_active = False
            self.save()
            return True
        return False
    
    def can_use(self):
        """Check if OD wallet can be used (active and has balance and not expired)"""
        if self.is_expired():
            return False
        return self.is_active and self.balance > 0
    
    def add_balance(self, amount, transaction_type='recharge', description='', reference_id=None):
        """Add balance to OD wallet and create transaction record (Admin only)"""
        if amount <= 0:
            raise ValidationError(_('Amount must be greater than zero'))
        
        if (self.balance + amount) > self.max_balance:
            raise ValidationError(_(f'Balance cannot exceed maximum limit of ₹{self.max_balance}'))
        
        # Track initial balance if this is first recharge or wallet is being activated
        if self.initial_balance == 0 or (not self.is_active and transaction_type == 'recharge'):
            self.initial_balance = self.balance + amount
        
        self.balance += amount
        self.save()
        
        # Create transaction record
        ODWalletTransaction.objects.create(
            od_wallet=self,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=self.balance,
            description=description,
            reference_id=reference_id
        )
        
        return self.balance
    
    def deduct_balance(self, amount, transaction_type='payment', description='', reference_id=None):
        """Deduct balance from OD wallet and create transaction record"""
        if amount <= 0:
            raise ValidationError(_('Amount must be greater than zero'))
        
        if amount > self.balance:
            raise ValidationError(_('Insufficient OD wallet balance'))
        
        if not self.is_active:
            raise ValidationError(_('OD Wallet is not active'))
        
        self.balance -= amount
        self.save()
        
        # Create transaction record (negative amount for deduction)
        ODWalletTransaction.objects.create(
            od_wallet=self,
            transaction_type=transaction_type,
            amount=-amount,
            balance_after=self.balance,
            description=description,
            reference_id=reference_id
        )
        
        return self.balance

class ODWalletTransaction(TimestampedModel):
    """Transaction history for OD Wallet"""
    class TransactionType(models.TextChoices):
        RECHARGE = 'recharge', _('Admin Recharge')
        PAYMENT = 'payment', _('Payment')
        REFUND = 'refund', _('Refund')
        ADJUSTMENT = 'adjustment', _('Admin Adjustment')
    
    od_wallet = models.ForeignKey(ODWallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(_('transaction type'), max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2, help_text=_('Positive for credit, negative for debit'))
    balance_after = models.DecimalField(_('balance after'), max_digits=10, decimal_places=2)
    description = models.TextField(_('description'), blank=True)
    reference_id = models.CharField(_('reference ID'), max_length=100, blank=True, null=True, help_text=_('Booking reference, payment ID, etc.'))
    
    class Meta:
        verbose_name = _('OD Wallet Transaction')
        verbose_name_plural = _('OD Wallet Transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['od_wallet', 'created_at'], name='od_wallet_transaction_idx'),
        ]
    
    def __str__(self):
        if self.amount is None:
            return f"{self.get_transaction_type_display()} - N/A"
        return f"{self.get_transaction_type_display()} - ₹{abs(self.amount)} - {self.od_wallet.user.email if self.od_wallet else 'N/A'}"
    
    @property
    def is_credit(self):
        """Check if transaction is a credit (positive amount)"""
        if self.amount is None:
            return False
        return self.amount > 0
    
    @property
    def is_debit(self):
        """Check if transaction is a debit (negative amount)"""
        if self.amount is None:
            return False
        return self.amount < 0

class CashBalanceWallet(TimestampedModel):
    """Cash Balance Wallet - User can recharge themselves, direct access for everyone"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cash_balance_wallet')
    balance = models.DecimalField(_('balance'), max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    max_balance = models.DecimalField(_('maximum balance'), max_digits=10, decimal_places=2, default=100000, validators=[MinValueValidator(0)], help_text=_('Maximum balance limit'))
    
    class Meta:
        verbose_name = _('Cash Balance Wallet')
        verbose_name_plural = _('Cash Balance Wallets')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Cash Balance - {self.user.email} (₹{self.balance})"
    
    def can_use(self):
        """Check if cash balance wallet can be used (has balance)"""
        return self.balance > 0
    
    def add_balance(self, amount, transaction_type='recharge', description='', reference_id=None):
        """Add balance to cash balance wallet and create transaction record (User self-recharge)"""
        if amount <= 0:
            raise ValidationError(_('Amount must be greater than zero'))
        
        if (self.balance + amount) > self.max_balance:
            raise ValidationError(_(f'Balance cannot exceed maximum limit of ₹{self.max_balance}'))
        
        self.balance += amount
        self.save()
        
        # Create transaction record
        CashBalanceTransaction.objects.create(
            cash_balance_wallet=self,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=self.balance,
            description=description,
            reference_id=reference_id
        )
        
        return self.balance
    
    def deduct_balance(self, amount, transaction_type='payment', description='', reference_id=None):
        """Deduct balance from cash balance wallet and create transaction record"""
        if amount <= 0:
            raise ValidationError(_('Amount must be greater than zero'))
        
        if amount > self.balance:
            raise ValidationError(_('Insufficient cash balance'))
        
        self.balance -= amount
        self.save()
        
        # Create transaction record (negative amount for deduction)
        CashBalanceTransaction.objects.create(
            cash_balance_wallet=self,
            transaction_type=transaction_type,
            amount=-amount,
            balance_after=self.balance,
            description=description,
            reference_id=reference_id
        )
        
        return self.balance

class CashBalanceTransaction(TimestampedModel):
    """Balance History Details - Complete transaction history for Cash Balance"""
    class TransactionType(models.TextChoices):
        RECHARGE = 'recharge', _('Recharge')
        PAYMENT = 'payment', _('Payment')
        REFUND = 'refund', _('Refund')
        ADJUSTMENT = 'adjustment', _('Adjustment')
    
    cash_balance_wallet = models.ForeignKey(CashBalanceWallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(_('transaction type'), max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2, help_text=_('Positive for credit, negative for debit'))
    balance_after = models.DecimalField(_('balance after'), max_digits=10, decimal_places=2)
    description = models.TextField(_('description'), blank=True)
    reference_id = models.CharField(_('reference ID'), max_length=100, blank=True, null=True, help_text=_('Booking reference, payment ID, etc.'))
    
    class Meta:
        verbose_name = _('Balance History Detail')
        verbose_name_plural = _('Balance History Details')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cash_balance_wallet', 'created_at'], name='cash_balance_transaction_idx'),
        ]
    
    def __str__(self):
        if self.amount is None:
            return f"{self.get_transaction_type_display()} - N/A"
        return f"{self.get_transaction_type_display()} - ₹{abs(self.amount)} - {self.cash_balance_wallet.user.email if self.cash_balance_wallet else 'N/A'}"
    
    @property
    def is_credit(self):
        """Check if transaction is a credit (positive amount)"""
        if self.amount is None:
            return False
        return self.amount > 0
    
    @property
    def is_debit(self):
        """Check if transaction is a debit (negative amount)"""
        if self.amount is None:
            return False
        return self.amount < 0

class SalesRepresentative(TimestampedModel):
    """Sales Representative model for user assignment and homepage display"""
    name = models.CharField(_('name'), max_length=100)
    phone = models.CharField(_('phone number'), max_length=20, help_text=_('Contact number'))
    is_active = models.BooleanField(_('active'), default=True, help_text=_('Show on homepage'))
    display_order = models.PositiveIntegerField(_('display order'), default=0, help_text=_('Order in which sales representatives are displayed'))
    
    class Meta:
        verbose_name = _('Sales Representative')
        verbose_name_plural = _('Sales Representatives')
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'display_order'], name='salesrep_active_idx'),
        ]
        db_table = 'travels_executive'  # Keep the same table name to preserve existing data
    
    def __str__(self):
        return f"{self.name} ({self.phone})"

class PackageApplication(TimestampedModel):
    """Model to store package application details"""
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONTACTED = 'contacted', _('Contacted')
        PROCESSING = 'processing', _('Processing')
        CONFIRMED = 'confirmed', _('Confirmed')
        CANCELLED = 'cancelled', _('Cancelled')
    
    # Package Information
    package_name = models.CharField(_('package name'), max_length=200, help_text=_('Name of the package (e.g., Thailand, Dubai, Singapore, Bali, Vietnam)'))
    destination = models.CharField(_('destination'), max_length=200)
    
    # User Information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='package_applications', verbose_name=_('user'))
    full_name = models.CharField(_('full name'), max_length=200)
    email = models.EmailField(_('email address'))
    phone = models.CharField(_('phone number'), max_length=20)
    
    # Travel Details
    travel_date = models.DateField(_('travel date'), null=True, blank=True)
    number_of_people = models.PositiveIntegerField(_('number of people'), default=1, validators=[MinValueValidator(1), MaxValueValidator(50)])
    special_requests = models.TextField(_('special requests'), blank=True)
    
    # Status and Admin
    status = models.CharField(_('status'), max_length=20, choices=Status.choices, default=Status.PENDING)
    admin_notes = models.TextField(_('admin notes'), blank=True, help_text=_('Internal notes for admin use'))
    estimated_amount = models.DecimalField(_('estimated amount'), max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Additional Information
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    
    class Meta:
        verbose_name = _('Package Application')
        verbose_name_plural = _('Package Applications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status', 'created_at'], name='package_application_idx'),
            models.Index(fields=['status', 'created_at'], name='package_application_status_idx'),
            models.Index(fields=['package_name'], name='package_application_name_idx'),
        ]
    
    def __str__(self):
        return f"Package Application - {self.package_name} - {self.full_name} ({self.get_status_display()})"
    
    @property
    def is_new(self):
        """Check if application is new"""
        return self.status == self.Status.PENDING
    
    @property
    def is_contacted(self):
        """Check if application has been contacted"""
        return self.status in [self.Status.CONTACTED, self.Status.PROCESSING, self.Status.CONFIRMED]

class GroupRequest(TimestampedModel):
    """B2B Group booking requests for bulk tickets (more than 9 passengers)"""
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONTACTED = 'contacted', _('Contacted')
        PROCESSING = 'processing', _('Processing')
        CONFIRMED = 'confirmed', _('Confirmed')
        CANCELLED = 'cancelled', _('Cancelled')
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_requests')
    reference_id = models.CharField(_('reference ID'), max_length=50, unique=True, editable=False)
    
    # Contact Information
    contact_name = models.CharField(_('contact name'), max_length=200)
    contact_email = models.EmailField(_('contact email'))
    contact_phone = models.CharField(_('contact phone'), max_length=20)
    company_name = models.CharField(_('company name'), max_length=200, blank=True)
    
    # Travel Details
    origin = models.CharField(_('origin'), max_length=100)
    destination = models.CharField(_('destination'), max_length=100)
    departure_date = models.DateField(_('departure date'))
    return_date = models.DateField(_('return date'), null=True, blank=True)
    trip_type = models.CharField(_('trip type'), max_length=20, choices=[('one_way', 'One Way'), ('return', 'Return')], default='one_way')
    travel_class = models.CharField(_('travel class'), max_length=20, choices=[('economy', 'Economy'), ('business', 'Business'), ('first', 'First')], default='economy')
    
    # Passenger Details
    number_of_passengers = models.PositiveIntegerField(_('number of passengers'), validators=[MinValueValidator(10)])
    adults = models.PositiveIntegerField(_('adults'), default=0)
    children = models.PositiveIntegerField(_('children'), default=0)
    infants = models.PositiveIntegerField(_('infants'), default=0)
    
    # Additional Information
    special_requirements = models.TextField(_('special requirements'), blank=True, help_text=_('Dietary requirements, wheelchair assistance, etc.'))
    additional_notes = models.TextField(_('additional notes'), blank=True)
    
    # Status and Admin
    status = models.CharField(_('status'), max_length=20, choices=Status.choices, default=Status.PENDING)
    admin_notes = models.TextField(_('admin notes'), blank=True, help_text=_('Internal notes for admin use'))
    estimated_amount = models.DecimalField(_('estimated amount'), max_digits=12, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name = _('group request')
        verbose_name_plural = _('group requests')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status', 'created_at'], name='group_request_idx'),
            models.Index(fields=['status', 'created_at'], name='group_request_status_idx'),
        ]
    
    def save(self, *args, **kwargs):
        if not self.reference_id:
            # Generate unique reference ID: GR + timestamp + random
            import random
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_str = str(random.randint(1000, 9999))
            self.reference_id = f'GR{timestamp}{random_str}'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Group Request {self.reference_id} - {self.contact_name} ({self.number_of_passengers} passengers)"


class Umrah(TimestampedModel):
    """Umrah package inquiry/application model"""
    
    class DurationChoices(models.TextChoices):
        DAYS_14 = '14', _('14 Days')
        DAYS_20 = '20', _('20 Days')
    
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONTACTED = 'contacted', _('Contacted')
        CONFIRMED = 'confirmed', _('Confirmed')
        CANCELLED = 'cancelled', _('Cancelled')
    
    # Personal Information
    full_name = models.CharField(_('Full Name'), max_length=200)
    email = models.EmailField(_('Email Address'))
    phone = models.CharField(_('Phone Number'), max_length=20)
    passport_size_photo = models.ImageField(
        _('Passport Size Photo'),
        upload_to='umrah/passport_photos/',
        blank=True,
        null=True,
        help_text=_('Upload passport size photo (Required)')
    )
    
    # Umrah Details
    duration = models.CharField(
        _('Duration'),
        max_length=10,
        choices=DurationChoices.choices,
        default=DurationChoices.DAYS_14
    )
    preferred_date = models.DateField(_('Preferred Travel Date'))
    number_of_passengers = models.PositiveIntegerField(_('Number of Passengers'), default=1)
    
    # Additional Information
    special_requests = models.TextField(_('Special Requests or Requirements'), blank=True, null=True)
    notes = models.TextField(_('Admin Notes'), blank=True, null=True)
    
    # Status
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING
    )
    
    # Reference ID
    reference_id = models.CharField(_('Reference ID'), max_length=50, unique=True, blank=True, editable=False)
    
    class Meta:
        verbose_name = _('Umrah Application')
        verbose_name_plural = _('Umrah Applications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='umrah_status_idx'),
            models.Index(fields=['duration', 'preferred_date'], name='umrah_duration_date_idx'),
        ]
    
    def save(self, *args, **kwargs):
        if not self.reference_id:
            # Generate unique reference ID: UM + timestamp + random
            import random
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_str = str(random.randint(1000, 9999))
            self.reference_id = f'UM{timestamp}{random_str}'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Umrah {self.reference_id} - {self.full_name} ({self.get_duration_display()})"


