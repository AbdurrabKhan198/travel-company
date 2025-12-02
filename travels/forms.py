from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import User, UserProfile, Booking, Package, Route, Schedule, BookingPassenger, Contact
from datetime import date
from decimal import Decimal
import re

User = get_user_model()

class UserRegisterForm(UserCreationForm):
    """Form for user registration with email, phone, and password fields"""
    email = forms.EmailField(
        label=_('Email Address'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email address'),
            'autocomplete': 'email',
            'required': 'required',
        }),
        error_messages={
            'required': _('Email is required'),
            'invalid': _('Enter a valid email address'),
        }
    )
    
    TITLE_CHOICES = [
        ('Mr', _('Mr')),
        ('Mrs', _('Mrs')),
        ('Miss', _('Miss')),
        ('Ms', _('Ms')),
        ('Dr', _('Dr')),
    ]
    
    title = forms.ChoiceField(
        label=_('Title'),
        choices=TITLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': 'required',
        }),
        initial='Mr'
    )
    
    full_name = forms.CharField(
        label=_('Full Name'),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your full name'),
            'required': 'required',
        })
    )
    
    gst_number = forms.CharField(
        label=_('GST Number'),
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter GST number (Optional)'),
        }),
        help_text=_('GST number (Optional) - Format: 27ABCDE1234F1Z5')
    )
    
    phone_regex = RegexValidator(
        regex=r'^\d{10,15}$',
        message=_("Phone number must contain only digits (10-15 digits allowed).")
    )
    
    phone = forms.CharField(
        label=_('Phone Number'),
        validators=[phone_regex],
        max_length=15,
        min_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g. 9876543210'),
            'autocomplete': 'tel',
            'pattern': r'\d{10,15}',
        }),
        required=True,
        help_text=_('Enter your phone number (10-15 digits only, no spaces or special characters)')
    )
    
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Create a strong password'),
            'autocomplete': 'new-password',
        }),
        help_text=_(
            'Your password must contain at least 8 characters, including at least one uppercase letter, '
            'one lowercase letter, one number, and one special character.'
        ),
        validators=[
            MinLengthValidator(8, _('Password must be at least 8 characters long.')),
        ]
    )
    
    password2 = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirm your password'),
            'autocomplete': 'new-password',
        }),
        help_text=_('Enter the same password as before, for verification.')
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('I agree to the Terms of Service and Privacy Policy'),
        error_messages={
            'required': _('You must accept the terms and conditions to register')
        }
    )
    
    
    # Company Details Fields (All Mandatory)
    company_name = forms.CharField(
        label=_('Company Name'),
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your company name'),
            'required': 'required',
        }),
        help_text=_('Name of your company'),
        error_messages={
            'required': _('Company name is required')
        }
    )
    
    address = forms.CharField(
        label=_('Address'),
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Enter your company address'),
            'required': 'required',
        }),
        help_text=_('Company address'),
        error_messages={
            'required': _('Address is required')
        }
    )
    
    city = forms.CharField(
        label=_('City'),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter city'),
            'required': 'required',
        }),
        error_messages={
            'required': _('City is required')
        }
    )
    
    state = forms.CharField(
        label=_('State/Province'),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter state/province'),
            'required': 'required',
        }),
        error_messages={
            'required': _('State/Province is required')
        }
    )
    
    country = forms.CharField(
        label=_('Country'),
        max_length=100,
        required=True,
        initial='India',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter country'),
            'required': 'required',
        }),
        error_messages={
            'required': _('Country is required')
        }
    )
    
    pincode = forms.CharField(
        label=_('Pin Code'),
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter pin code'),
            'pattern': r'\d{6}',
            'required': 'required',
        }),
        help_text=_('6-digit pin code'),
        error_messages={
            'required': _('Pin code is required')
        }
    )
    
    aadhar_card = forms.ImageField(
        label=_('Aadhar Card'),
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'required': 'required',
        }),
        help_text=_('Upload your Aadhar card image (Required)'),
        error_messages={
            'required': _('Aadhar card upload is mandatory')
        }
    )
    
    class Meta:
        model = User
        fields = ('email', 'phone', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove default help text for username field
        if 'username' in self.fields:
            self.fields['username'].help_text = ''
    
    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('This email is already registered. Please use a different email or try logging in.'))
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        if not phone:
            raise ValidationError(_('Phone number is required'))
        if len(phone) < 10 or len(phone) > 15:
            raise ValidationError(_('Phone number must be between 10 and 15 digits'))
        if User.objects.filter(phone=phone).exists():
            raise ValidationError(_('This phone number is already registered. Please use a different number or try logging in.'))
        return phone
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        # Password complexity validation
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password1):
            raise ValidationError(_(
                'Password must contain at least 8 characters, including at least one uppercase letter, '
                'one lowercase letter, one number, and one special character.'
            ))
        return password1
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('password2', _("The two password fields didn't match."))
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data.get('phone', '')
        
        if commit:
            user.save()
            # Get or create user profile (signal might have already created it)
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'title': self.cleaned_data.get('title', 'Mr'),
                    'full_name': self.cleaned_data['full_name'],
                    'gst_number': self.cleaned_data.get('gst_number', ''),
                    'company_name': self.cleaned_data.get('company_name', ''),
                    'address': self.cleaned_data.get('address', ''),
                    'city': self.cleaned_data.get('city', ''),
                    'state': self.cleaned_data.get('state', ''),
                    'country': self.cleaned_data.get('country', 'India'),
                    'pincode': self.cleaned_data.get('pincode', '')
                }
            )
            
            # Update profile with all fields (including file uploads)
            if not created:
                profile.title = self.cleaned_data.get('title', 'Mr')
                profile.full_name = self.cleaned_data['full_name']
                profile.gst_number = self.cleaned_data.get('gst_number', '')
                profile.company_name = self.cleaned_data.get('company_name', '')
                profile.address = self.cleaned_data.get('address', '')
                profile.city = self.cleaned_data.get('city', '')
                profile.state = self.cleaned_data.get('state', '')
                profile.country = self.cleaned_data.get('country', 'India')
                profile.pincode = self.cleaned_data.get('pincode', '')
            
            # Handle file uploads
            if self.cleaned_data.get('aadhar_card'):
                profile.aadhar_card = self.cleaned_data.get('aadhar_card')
            
            profile.save()
        return user
    
    def clean_gst_number(self):
        gst = self.cleaned_data.get('gst_number', '').strip()
        if gst:
            # GST format: 27ABCDE1234F1Z5 (15 characters)
            if len(gst) != 15:
                raise ValidationError(_('GST number must be 15 characters long'))
            # Basic format validation: 2 digits + 5 letters + 4 digits + 1 letter + 1 digit + Z + 1 letter + 1 digit
            import re
            if not re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$', gst.upper()):
                raise ValidationError(_('Please enter a valid GST number format (e.g., 27ABCDE1234F1Z5)'))
            # Check if GST is already registered
            if UserProfile.objects.filter(gst_number__iexact=gst).exists():
                raise ValidationError(_('This GST number is already registered. Please use a different number or try logging in.'))
            return gst.upper()
        return gst


class UserLoginForm(AuthenticationForm):
    """Form for user login with email and password"""
    username = forms.EmailField(
        label=_('Email Address'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email address'),
            'autocomplete': 'email',
            'autofocus': True,
        })
    )
    
    password = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your password'),
            'autocomplete': 'current-password',
        })
    )
    
    remember_me = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Remember me')
    )
    
    error_messages = {
        'invalid_login': _(
            "Please enter a correct email and password. Note that both fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the username field's help text
        self.fields['username'].help_text = ''
    
    def clean_username(self):
        return self.cleaned_data['username'].lower()


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile information"""
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('First Name')
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Last Name')
        })
    )
    
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'max': str(date.today().strftime('%Y-%m-%d')),
        }),
        help_text=_('Format: YYYY-MM-DD')
    )
    
    profile_picture = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'onchange': 'previewImage(this)'
        }),
        help_text=_('Recommended size: 200x200 pixels, max 2MB')
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 
            'address', 'city', 'state', 'country', 'pincode', 'profile_picture'
        ]
        widgets = {
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Your full address')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('City'
            )}),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('State/Province'
            )}),
            'country': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_country'
            }),
            'pincode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Postal/ZIP Code')
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > date.today():
            raise ValidationError(_('Date of birth cannot be in the future'))
        return dob
    
    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode', '').strip()
        if pincode and not pincode.isdigit():
            raise ValidationError(_('Postal/ZIP code must contain only digits'))
        return pincode
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # Update the related user model
        if hasattr(profile, 'user'):
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            if commit:
                user.save()
        
        if commit:
            profile.save()
        return profile


class PasswordChangeCustomForm(forms.Form):
    """Form for changing user password"""
    current_password = forms.CharField(
        label=_('Current Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your current password'),
            'autocomplete': 'current-password',
        })
    )
    
    new_password1 = forms.CharField(
        label=_('New Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter new password'),
            'autocomplete': 'new-password',
        }),
        help_text=_(
            'Your password must contain at least 8 characters, including at least one uppercase letter, '
            'one lowercase letter, one number, and one special character.'
        ),
        validators=[
            MinLengthValidator(8, _('Password must be at least 8 characters long.')),
        ]
    )
    
    new_password2 = forms.CharField(
        label=_('Confirm New Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirm new password'),
            'autocomplete': 'new-password',
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError(_('Your current password was entered incorrectly. Please enter it again.'))
        return current_password
    
    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        # Password complexity validation
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password1):
            raise ValidationError(_(
                'Password must contain at least 8 characters, including at least one uppercase letter, '
                'one lowercase letter, one number, and one special character.'
            ))
        return password1
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('new_password2', _("The two password fields didn't match."))
        
        return cleaned_data
    
    def save(self, commit=True):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


class PasswordResetRequestForm(PasswordResetForm):
    """Form for requesting a password reset"""
    email = forms.EmailField(
        label=_('Email Address'),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email address'),
            'autocomplete': 'email',
            'autofocus': True,
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise ValidationError(_("There is no user registered with the specified email address!"))
        return email


class SetNewPasswordForm(SetPasswordForm):
    """Form for setting a new password after password reset"""
    new_password1 = forms.CharField(
        label=_('New Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter new password'),
            'autocomplete': 'new-password',
        }),
        help_text=_(
            'Your password must contain at least 8 characters, including at least one uppercase letter, '
            'one lowercase letter, one number, and one special character.'
        ),
        validators=[
            MinLengthValidator(8, _('Password must be at least 8 characters long.')),
        ]
    )
    
    new_password2 = forms.CharField(
        label=_('Confirm New Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirm new password'),
            'autocomplete': 'new-password',
        })
    )
    
    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        # Password complexity validation
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password1):
            raise ValidationError(_(
                'Password must contain at least 8 characters, including at least one uppercase letter, '
                'one lowercase letter, one number, and one special character.'
            ))
        return password1


class BookingForm(forms.ModelForm):
    """Form for creating a new booking"""
    class Meta:
        model = Booking
        fields = [
            'schedule', 'contact_email', 'contact_phone', 'special_requests'
        ]
        widgets = {
            'schedule': forms.HiddenInput(),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': 'Your email address'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'required': True,
                'placeholder': 'Your phone number'
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any special requests or notes'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values if user is authenticated
        if self.user and self.user.is_authenticated:
            self.fields['contact_email'].initial = self.user.email
            if hasattr(self.user, 'profile') and self.user.profile.phone:
                self.fields['contact_phone'].initial = self.user.profile.phone
    
    def clean_schedule(self):
        schedule = self.cleaned_data.get('schedule')
        if not schedule or not schedule.is_available:
            raise ValidationError(_('The selected schedule is no longer available.'))
        return schedule


class PackageBookingForm(forms.Form):
    """Form for booking a travel package"""
    contact_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'required': True,
            'placeholder': _('Your email address')
        })
    )
    contact_phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'required': True,
            'placeholder': _('Your phone number')
        })
    )
    number_of_people = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 20,
        })
    )
    travel_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': str(date.today().strftime('%Y-%m-%d')),
        })
    )
    special_requests = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Any special requests or requirements?')
        })
    )
    package_id = forms.IntegerField(widget=forms.HiddenInput())
    
    def __init__(self, *args, **kwargs):
        self.package = kwargs.pop('package', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and self.user.is_authenticated:
            self.fields['contact_email'].initial = self.user.email
            if hasattr(self.user, 'profile') and self.user.profile.phone:
                self.fields['contact_phone'].initial = self.user.profile.phone
        
        if self.package:
            self.fields['package_id'].initial = self.package.id
            # Set a default travel date (e.g., 30 days from now)
            from datetime import timedelta
            default_date = date.today() + timedelta(days=30)
            self.fields['travel_date'].initial = default_date
    
    def clean_travel_date(self):
        travel_date = self.cleaned_data.get('travel_date')
        if travel_date < date.today():
            raise ValidationError(_('Travel date cannot be in the past'))
        return travel_date
    
    def clean_number_of_people(self):
        number_of_people = self.cleaned_data.get('number_of_people', 1)
        if number_of_people < 1 or number_of_people > 20:
            raise ValidationError(_('Number of people must be between 1 and 20'))
        return number_of_people


class ContactForm(forms.Form):
    """Contact form for the website"""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Your Name'),
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Your Email'),
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Your Phone (Optional)'),
        })
    )
    
    subject = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Subject (Optional)'),
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': _('Your Message'),
        })
    )
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError(_('Name is required'))
        return name
    
    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise ValidationError(_('Message is too short. Please provide more details.'))
        return message

class WalletRechargeForm(forms.Form):
    """Form for recharging wallet balance"""
    amount = forms.DecimalField(
        label=_('Recharge Amount'),
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('100.00'),
        max_value=Decimal('100000.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter amount (min ₹100, max ₹1,00,000)'),
            'step': '0.01',
            'min': '100',
            'max': '100000',
        }),
        help_text=_('Minimum recharge: ₹100, Maximum: ₹1,00,000')
    )
    
    description = forms.CharField(
        label=_('Description (Optional)'),
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Add a note for this recharge'),
        })
    )
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount < Decimal('100.00'):
            raise ValidationError(_('Minimum recharge amount is ₹100'))
        if amount > Decimal('100000.00'):
            raise ValidationError(_('Maximum recharge amount is ₹1,00,000'))
        return amount
