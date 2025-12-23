from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse, path
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import render
from django.db.models import Sum, Count

from .models import (
    User, UserProfile, Route, Schedule, Booking, BookingPassenger,
    Package, Contact, ODWallet, ODWalletTransaction, 
    CashBalanceWallet, CashBalanceTransaction, GroupRequest, PackageApplication, SalesRepresentative, Umrah, Coupon, VisaBooking, BookingChangeRequest
)

# Custom Admin Filter for Agency ID
class AgencyIDFilter(admin.SimpleListFilter):
    title = _('Agency ID')
    parameter_name = 'agency_id'

    def lookups(self, request, model_admin):
        # Get all unique agency IDs from user profiles who have cash balance wallets (newest first)
        agency_ids = UserProfile.objects.filter(
            user__cash_balance_wallet__isnull=False
        ).order_by('-created_at').values_list('client_id', flat=True).distinct()
        return [(agency_id, agency_id) for agency_id in agency_ids if agency_id]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(cash_balance_wallet__user__profile__client_id=self.value())

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Agency Details'
    fk_name = 'user'
    extra = 0
    readonly_fields = ('created_at', 'updated_at')

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for Staff and Admin users only - NOT agencies"""
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_superuser', 'is_active', 'last_login')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone')}),
        (_('Account Status'), {
            'fields': ('is_active',),
        }),
        (_('Permissions'), {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions', 'user_type'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type'),
        }),
    )
    
    def get_queryset(self, request):
        """Only show staff/superuser accounts - hide agencies"""
        qs = super().get_queryset(request)
        return qs.filter(is_staff=True) | qs.filter(is_superuser=True)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for Agencies/Customers - NOT staff/admin accounts"""
    list_display = (
        'agency_id_display', 'user_email', 'full_name', 'company_name', 
        'city', 'is_approved_badge', 'is_verified', 'sales_rep_display', 
        'wallet_balance_display', 'created_at_display'
    )
    search_fields = ('user__email', 'client_id', 'full_name', 'gst_number', 'id_number', 'city', 'country', 'company_name')
    list_filter = ('is_approved', 'is_verified', 'country', 'city', 'sales_representative', 'gender', 'id_type')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('🏢 Agency Account', {
            'fields': ('user', 'client_id', 'is_approved', 'is_verified', 'sales_representative'),
            'description': 'Manage agency account status. Agency can only login if approved.'
        }),
        ('👤 Owner/Contact Details', {
            'fields': ('title', 'full_name', 'date_of_birth', 'gender', 'profile_picture')
        }),
        ('📍 Address', {
            'fields': ('address', 'city', 'state', 'country', 'pincode')
        }),
        ('🏛️ Company Information', {
            'fields': ('company_name', 'gst_number', 'logo'),
        }),
        ('📄 Aadhar Card Documents', {
            'fields': ('aadhar_card_front', 'aadhar_card_back'),
            'description': 'Aadhar card images uploaded during signup for verification.'
        }),
        ('📄 Identification', {
            'fields': ('id_type', 'id_number'),
            'classes': ('collapse',)
        }),
        ('📁 PDF Documents', {
            'fields': ('id_document_pdf', 'passport_pdf', 'other_documents'),
            'classes': ('collapse',),
        }),
        ('⏱️ Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'client_id', 'profile_picture_preview', 'has_pdfs')
    actions = ['approve_agencies', 'unapprove_agencies', 'verify_agencies', 'unverify_agencies']
    
    def get_queryset(self, request):
        """Only show non-staff user profiles (agencies only)"""
        qs = super().get_queryset(request)
        return qs.filter(user__is_staff=False, user__is_superuser=False)
    
    def agency_id_display(self, obj):
        return format_html(
            '<span style="font-weight: bold; color: #2563eb; background: #dbeafe; padding: 3px 8px; border-radius: 4px;">{}</span>',
            obj.client_id if obj.client_id else 'N/A'
        )
    agency_id_display.short_description = 'Agency ID'
    agency_id_display.admin_order_field = 'client_id'
    
    def user_email(self, obj):
        if obj.user:
            return format_html('<a href="/admin/travels/userprofile/{}/change/">{}</a>', obj.id, obj.user.email)
        return 'N/A'
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    
    def is_approved_badge(self, obj):
        if obj.is_approved:
            return format_html('<span style="background: #22c55e; color: white; padding: 3px 8px; border-radius: 10px;">✓ Yes</span>')
        return format_html('<span style="background: #ef4444; color: white; padding: 3px 8px; border-radius: 10px;">✗ No</span>')
    is_approved_badge.short_description = 'Approved'
    is_approved_badge.admin_order_field = 'is_approved'
    
    def wallet_balance_display(self, obj):
        try:
            if hasattr(obj.user, 'cash_balance_wallet'):
                balance = obj.user.cash_balance_wallet.balance
                return format_html('<span style="font-weight: bold; color: #059669;">₹{:.2f}</span>', float(balance))
        except:
            pass
        return '₹0.00'
    wallet_balance_display.short_description = 'Wallet'
    
    def created_at_display(self, obj):
        return obj.created_at.strftime('%d %b %Y')
    created_at_display.short_description = 'Joined'
    created_at_display.admin_order_field = 'created_at'
    
    def sales_rep_display(self, obj):
        if obj.sales_representative:
            return obj.sales_representative.name
        return '-'
    sales_rep_display.short_description = 'Sales Rep'
    
    def approve_agencies(self, request, queryset):
        """Approve selected agencies and send approval emails"""
        count = 0
        for profile in queryset:
            if not profile.is_approved:
                profile.is_approved = True
                profile.save()
                count += 1
        self.message_user(request, f'{count} agency(ies) approved successfully. Approval emails sent.')
    approve_agencies.short_description = '✅ Approve selected agencies'
    
    def unapprove_agencies(self, request, queryset):
        """Unapprove selected agencies"""
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} agency(ies) unapproved.')
    unapprove_agencies.short_description = '❌ Unapprove selected agencies'
    
    def verify_agencies(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} agency(ies) verified.')
    verify_agencies.short_description = '✔️ Verify selected agencies'
    
    def unverify_agencies(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} agency(ies) unverified.')
    unverify_agencies.short_description = '✖️ Unverify selected agencies'
    
    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                obj.profile_picture.url
            )
        return "No image"
    profile_picture_preview.short_description = 'Profile Picture Preview'
    
    def has_pdfs(self, obj):
        pdfs = []
        if obj.id_document_pdf:
            pdfs.append(format_html('<a href="{}" target="_blank">ID Document</a>', obj.id_document_pdf.url))
        if obj.passport_pdf:
            pdfs.append(format_html('<a href="{}" target="_blank">Passport</a>', obj.passport_pdf.url))
        if obj.other_documents:
            pdfs.append(format_html('<a href="{}" target="_blank">Other</a>', obj.other_documents.url))
        return format_html('<br>'.join(pdfs)) if pdfs else "No PDFs"
    has_pdfs.short_description = 'PDF Documents'

class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1
    readonly_fields = ('created_at', 'updated_at')
    fields = ('departure_date', 'arrival_date', 'pnr', 'total_seats', 'available_seats', 'adult_fare', 'child_fare', 'infant_fare', 'is_active', 'notes')

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'airline_name', 'from_location', 'to_location', 'transport_type', 'duration_formatted', 'is_non_refundable', 'is_active')
    list_filter = ('transport_type', 'route_type', 'is_active', 'is_non_refundable', 'airline_name')
    search_fields = ('name', 'from_location', 'to_location', 'carrier_number', 'airline_name')
    inlines = [ScheduleInline]
    readonly_fields = ('created_at', 'updated_at', 'duration_formatted')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'from_location', 'to_location', 'transport_type', 'airline_name', 'carrier_number', 'route_type')
        }),
        ('Schedule', {
            'fields': ('departure_time', 'arrival_time', 'duration')
        }),
        ('Terminal Information', {
            'fields': ('departure_terminal', 'arrival_terminal')
        }),
        ('Status', {
            'fields': ('is_non_refundable', 'is_active')
        }),
        ('Additional Information', {
            'fields': ('description', 'amenities'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'duration_formatted'),
            'classes': ('collapse',)
        }),
    )
    
    def duration_formatted(self, obj):
        return obj.formatted_duration
    duration_formatted.short_description = 'Duration'

# ScheduleAdmin removed - Schedules are now managed only through Route inline
# This prevents confusion - all schedule management happens within Route edit page
# @admin.register(Schedule)
# class ScheduleAdmin(admin.ModelAdmin):
#     ... (commented out to avoid confusion)

class BookingPassengerInline(admin.TabularInline):
    model = BookingPassenger
    extra = 0
    readonly_fields = ('full_name', 'pnr', 'age', 'passenger_type')
    can_delete = False
    
    def has_add_permission(self, request, obj):
        return False

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'user_email', 'schedule_info', 'status', 'payment_status', 'total_amount', 'created_at')
    list_filter = ('status', 'payment_status', 'schedule__route__transport_type')
    search_fields = ('booking_reference', 'user__email', 'contact_email', 'contact_phone')
    readonly_fields = ('booking_reference', 'created_at', 'updated_at', 'user_email', 'schedule_info')
    inlines = [BookingPassengerInline]
    date_hierarchy = 'created_at'
    actions = ['mark_as_confirmed', 'mark_as_cancelled', 'export_bookings']
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_reference', 'user_email', 'schedule_info', 'status', 'payment_status')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone')
        }),
        ('Financial Information', {
            'fields': ('base_fare', 'tax_amount', 'discount_amount', 'total_amount', 'currency')
        }),
        ('Additional Information', {
            'fields': ('special_requests', 'notes')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'ip_address')
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email if obj.user else 'Guest'
    user_email.short_description = 'User'
    
    def schedule_info(self, obj):
        return f"{obj.schedule.route} on {obj.schedule.departure_date}"
    schedule_info.short_description = 'Schedule'
    
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f"{updated} bookings marked as confirmed.")
    mark_as_confirmed.short_description = "Mark selected bookings as confirmed"
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"{updated} bookings marked as cancelled.")
    mark_as_cancelled.short_description = "Mark selected bookings as cancelled"
    
    def export_bookings(self, request, queryset):
        # This is a placeholder - in a real app, you'd generate a CSV/Excel file
        self.message_user(request, "Export functionality would be implemented here")
    export_bookings.short_description = "Export selected bookings"

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'destination', 'package_type', 'duration_display', 'base_price', 'discounted_price', 'is_featured', 'is_active')
    list_filter = ('package_type', 'is_featured', 'is_active')
    search_fields = ('title', 'destination', 'short_description')
    prepopulated_fields = {'slug': ('title', 'destination')}
    readonly_fields = ('created_at', 'updated_at', 'meta_preview', 'discounted_price')
    save_on_top = True
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'destination', 'package_type', 'is_featured', 'is_active')
        }),
        ('Pricing', {
            'fields': ('base_price', 'discount_percentage')
        }),
        ('Duration', {
            'fields': ('duration_days', 'duration_nights')
        }),
        ('Content', {
            'fields': ('short_description', 'description', 'main_image', 'itinerary', 'inclusions', 'exclusions')
        }),
        ('SEO', {
            'classes': ('collapse',),
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'meta_preview')
        }),
        ('System Information', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def meta_preview(self, obj):
        if not obj.meta_title or not obj.meta_description:
            return "Save the package to see meta preview"
        return format_html(
            '<div style="max-width: 600px; border: 1px solid #ddd; padding: 10px; margin: 10px 0;">'
            '<div style="color: #1a0dab; font-size: 18px; margin-bottom: 5px;">{}</div>'
            '<div style="color: #006621; font-size: 14px; margin-bottom: 5px;">{}</div>'
            '<div style="color: #545454; font-size: 13px;">{}</div>'
            '</div>',
            obj.meta_title,
            f"https://safarzometravels.com/packages/{obj.slug}/",
            obj.meta_description[:160] + '...' if obj.meta_description and len(obj.meta_description) > 160 else obj.meta_description
        )
    meta_preview.short_description = 'Search Result Preview'
    
    def save_model(self, request, obj, form, change):
        if not obj.meta_title:
            obj.meta_title = f"{obj.title} - {obj.destination} | Safar Zone Travels"
        if not obj.meta_description:
            obj.meta_description = obj.short_description[:160]
        super().save_model(request, obj, form, change)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'status', 'created_at', 'is_new_badge')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at', 'updated_at', 'ip_address', 'user_agent')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone', 'subject', 'message')
        }),
        ('Status & Management', {
            'fields': ('status', 'admin_notes')
        }),
        ('System Information', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_new_badge(self, obj):
        if obj.is_new:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">NEW</span>'
            )
        return format_html(
            '<span style="background-color: #6b7280; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            obj.get_status_display()
        )
    is_new_badge.short_description = 'Status'
    
    actions = ['mark_as_read', 'mark_as_replied', 'mark_as_closed']
    
    def mark_as_read(self, request, queryset):
        queryset.update(status=Contact.Status.READ)
        self.message_user(request, f'{queryset.count()} inquiry(s) marked as read.')
    mark_as_read.short_description = 'Mark selected as read'
    
    def mark_as_replied(self, request, queryset):
        queryset.update(status=Contact.Status.REPLIED)
        self.message_user(request, f'{queryset.count()} inquiry(s) marked as replied.')
    mark_as_replied.short_description = 'Mark selected as replied'
    
    def mark_as_closed(self, request, queryset):
        queryset.update(status=Contact.Status.CLOSED)
        self.message_user(request, f'{queryset.count()} inquiry(s) marked as closed.')
    mark_as_closed.short_description = 'Mark selected as closed'

class ODWalletTransactionInline(admin.TabularInline):
    model = ODWalletTransaction
    extra = 0
    readonly_fields = ('transaction_type', 'amount', 'balance_after', 'description', 'reference_id', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj):
        return False

@admin.register(ODWallet)
class ODWalletAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'agency_id_display', 'balance_display', 'is_active', 'expiry_info', 'max_balance', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'user__profile__client_id')
    readonly_fields = ('created_at', 'updated_at', 'user_email', 'agency_id_display', 'transaction_count')
    autocomplete_fields = ['user']  # Make user field searchable with autocomplete
    inlines = [ODWalletTransactionInline]
    date_hierarchy = 'created_at'
    actions = ['activate_wallets', 'deactivate_wallets', 'recharge_wallets']
    
    def agency_id_display(self, obj):
        if obj.user and hasattr(obj.user, 'profile') and obj.user.profile.client_id:
            return obj.user.profile.client_id
        return 'N/A'
    agency_id_display.short_description = 'Agency ID'
    
    def balance_display(self, obj):
        if obj.balance < 0:
            return f"-₹{abs(obj.balance):.2f}"
        return f"₹{obj.balance:.2f}"
    balance_display.short_description = 'Balance'
    
    def expiry_info(self, obj):
        if obj.expires_at:
            if obj.is_expired():
                return f"Expired ({obj.days_remaining()} days ago)"
            days = obj.days_remaining()
            if days == 0:
                return "Expires Today"
            elif days == 1:
                return "1 Day Left"
            else:
                return f"{days} Days Left"
        return "No Expiry"
    expiry_info.short_description = 'Expiry Status'
    
    fieldsets = (
        ('OD Wallet Information', {
            'fields': ('user', 'balance', 'max_balance', 'is_active'),
            'description': 'OD Wallet can only be recharged by admin. Users can only use it when active.'
        }),
        ('Expiry Settings', {
            'fields': ('expiry_days', 'expires_at', 'initial_balance'),
            'description': 'Set expiry_days (e.g., 3 for 3 days). After expiry, remaining balance will be deducted and wallet deactivated. Initial balance is auto-tracked.',
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('transaction_count',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email if obj.user else 'N/A'
    user_email.short_description = 'User'
    
    def get_readonly_fields(self, request, obj=None):
        """Make user_email readonly when editing, but allow user selection when creating"""
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly.append('user')  # Make user readonly when editing
        return readonly
    
    def transaction_count(self, obj):
        return obj.transactions.count()
    transaction_count.short_description = 'Total Transactions'
    
    def activate_wallets(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} OD wallet(s) activated.")
    activate_wallets.short_description = "Activate selected OD wallets"
    
    def deactivate_wallets(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} OD wallet(s) deactivated.")
    deactivate_wallets.short_description = "Deactivate selected OD wallets"
    
    def recharge_wallets(self, request, queryset):
        # This is a placeholder - in production, you'd have a form to enter recharge amount
        self.message_user(request, "Use the 'Add Balance' action in the wallet detail page to recharge.")
    recharge_wallets.short_description = "Recharge selected OD wallets (use detail page)"

@admin.register(ODWalletTransaction)
class ODWalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet_user', 'transaction_type', 'amount_display', 'balance_after', 'reference_id', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('od_wallet__user__email', 'description', 'reference_id')
    readonly_fields = ('od_wallet', 'transaction_type', 'amount', 'balance_after', 'description', 'reference_id', 'created_at', 'updated_at', 'is_credit_display')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('od_wallet', 'transaction_type', 'amount', 'balance_after', 'is_credit_display')
        }),
        ('Details', {
            'fields': ('description', 'reference_id')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def wallet_user(self, obj):
        return obj.od_wallet.user.email if obj.od_wallet and obj.od_wallet.user else 'N/A'
    wallet_user.short_description = 'User'
    
    def amount_display(self, obj):
        if obj is None or obj.amount is None:
            return "N/A"
        if obj.amount > 0:
            return format_html('<span style="color: green;">+₹{}</span>', obj.amount)
        else:
            return format_html('<span style="color: red;">-₹{}</span>', abs(obj.amount))
    amount_display.short_description = 'Amount'
    
    def is_credit_display(self, obj):
        if obj is None or obj.amount is None:
            return "N/A"
        return "Credit" if obj.is_credit else "Debit"
    is_credit_display.short_description = 'Type'

class CashBalanceTransactionInline(admin.TabularInline):
    model = CashBalanceTransaction
    extra = 0
    readonly_fields = ('transaction_type', 'amount_display', 'balance_after', 'description', 'reference_id', 'created_at')
    fields = ('created_at', 'transaction_type', 'amount_display', 'balance_after', 'description', 'reference_id')
    can_delete = False
    verbose_name = 'Balance History Detail'
    verbose_name_plural = 'Complete Balance History Details'
    
    def amount_display(self, obj):
        if obj.amount > 0:
            return format_html('<span style="color: green; font-weight: bold;">+₹{}</span>', f'{float(obj.amount):.2f}')
        else:
            return format_html('<span style="color: red; font-weight: bold;">-₹{}</span>', f'{float(abs(obj.amount)):.2f}')
    amount_display.short_description = 'Amount'
    
    def has_add_permission(self, request, obj):
        return False

@admin.register(CashBalanceWallet)
class CashBalanceWalletAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'agency_id_display', 'balance_display', 'transaction_count', 'last_transaction', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'user__client_id', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'user_full_info', 'transaction_count', 'total_credits', 'total_debits', 'last_transaction_details')
    inlines = [CashBalanceTransactionInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user_full_info',),
            'description': 'Complete user details with balance information'
        }),
        ('Cash Balance Wallet Information', {
            'fields': ('balance', 'max_balance'),
            'description': 'Cash Balance Wallet - Users can recharge themselves. Direct access for everyone.'
        }),
        ('Transaction Statistics', {
            'fields': ('transaction_count', 'total_credits', 'total_debits', 'last_transaction_details'),
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        if obj.user:
            # Link to user profile instead of user
            if hasattr(obj.user, 'profile'):
                return format_html(
                    '<a href="/admin/travels/userprofile/{}/change/">{}</a>',
                    obj.user.profile.id, obj.user.email
                )
            return obj.user.email
        return 'N/A'
    user_email.short_description = 'User Email'
    
    def agency_id_display(self, obj):
        if obj.user and hasattr(obj.user, 'profile'):
            return getattr(obj.user.profile, 'client_id', 'N/A') or 'N/A'
        return 'N/A'
    agency_id_display.short_description = 'Agency ID'
    
    def balance_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #059669; font-size: 16px;">₹{}</span>', f'{float(obj.balance):.2f}')
    balance_display.short_description = 'Current Balance'
    
    def user_full_info(self, obj):
        if obj.user:
            user = obj.user
            profile = getattr(user, 'profile', None)
            info = f"""
            <div style="background: #f0f9ff; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6;">
                <h3 style="margin-top: 0; color: #1e40af;">Complete User Information</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px; font-weight: bold; width: 150px;">Email:</td>
                        <td style="padding: 8px;">{user.email}</td>
                    </tr>
                    <tr style="background: white;">
                        <td style="padding: 8px; font-weight: bold;">Agency ID:</td>
                        <td style="padding: 8px;">{profile.client_id if profile else 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Full Name:</td>
                        <td style="padding: 8px;">{profile.full_name if profile else 'N/A'}</td>
                    </tr>
                    <tr style="background: white;">
                        <td style="padding: 8px; font-weight: bold;">Phone:</td>
                        <td style="padding: 8px;">{user.phone if user.phone else 'N/A'}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Company:</td>
                        <td style="padding: 8px;">{profile.company_name if profile and profile.company_name else 'N/A'}</td>
                    </tr>
                    <tr style="background: white;">
                        <td style="padding: 8px; font-weight: bold;">User Type:</td>
                        <td style="padding: 8px;">{user.get_user_type_display()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Status:</td>
                        <td style="padding: 8px;">
                            <span style="background: {'#10b981' if user.is_approved else '#ef4444'}; color: white; padding: 3px 10px; border-radius: 4px;">
                                {'Approved' if user.is_approved else 'Pending'}
                            </span>
                        </td>
                    </tr>
                    <tr style="background: white;">
                        <td style="padding: 8px; font-weight: bold;">Current Balance:</td>
                        <td style="padding: 8px;">
                            <span style="font-size: 18px; font-weight: bold; color: #059669;">₹{obj.balance:.2f}</span>
                        </td>
                    </tr>
                </table>
            </div>
            """
            return format_html(info)
        return 'N/A'
    user_full_info.short_description = 'User Details'
    
    def transaction_count(self, obj):
        count = obj.transactions.count()
        return format_html('<span style="font-weight: bold; color: #3b82f6;">{}</span>', count)
    transaction_count.short_description = 'Total Transactions'
    
    def total_credits(self, obj):
        from django.db.models import Sum
        total = obj.transactions.filter(amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
        return format_html('<span style="color: green; font-weight: bold;">+₹{}</span>', f'{float(total):.2f}')
    total_credits.short_description = 'Total Credits'
    
    def total_debits(self, obj):
        from django.db.models import Sum
        total = obj.transactions.filter(amount__lt=0).aggregate(Sum('amount'))['amount__sum'] or 0
        return format_html('<span style="color: red; font-weight: bold;">-₹{}</span>', f'{float(abs(total)):.2f}')
    total_debits.short_description = 'Total Debits'
    
    def last_transaction(self, obj):
        last = obj.transactions.first()
        if last:
            return last.created_at.strftime('%Y-%m-%d %H:%M')
        return 'No transactions'
    last_transaction.short_description = 'Last Transaction'
    
    def last_transaction_details(self, obj):
        last = obj.transactions.first()
        if last:
            amount_color = 'green' if last.amount > 0 else 'red'
            amount_sign = '+' if last.amount > 0 else ''
            details = f"""
            <div style="background: #fef3c7; padding: 15px; border-radius: 5px; border-left: 4px solid #f59e0b;">
                <h4 style="margin-top: 0;">Last Transaction</h4>
                <p><strong>Type:</strong> {last.get_transaction_type_display()}</p>
                <p><strong>Amount:</strong> <span style="color: {amount_color}; font-weight: bold; font-size: 16px;">{amount_sign}₹{abs(last.amount):.2f}</span></p>
                <p><strong>Balance After:</strong> ₹{last.balance_after:.2f}</p>
                <p><strong>Date:</strong> {last.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Description:</strong> {last.description if last.description else 'N/A'}</p>
                <p><strong>Reference:</strong> {last.reference_id if last.reference_id else 'N/A'}</p>
            </div>
            """
            return format_html(details)
        return 'No transactions yet'
    last_transaction_details.short_description = 'Last Transaction Details'

@admin.register(CashBalanceTransaction)
class CashBalanceTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet_user', 'agency_id_clickable', 'transaction_type', 'amount_display', 'balance_after', 'description_short', 'reference_id', 'created_at')
    list_filter = (AgencyIDFilter, 'transaction_type', 'created_at')
    search_fields = ('cash_balance_wallet__user__email', 'cash_balance_wallet__user__profile__client_id', 'cash_balance_wallet__user__first_name', 'cash_balance_wallet__user__last_name', 'description', 'reference_id')
    readonly_fields = ('cash_balance_wallet', 'transaction_type', 'amount', 'balance_after', 'description', 'reference_id', 'created_at', 'updated_at', 'is_credit_display', 'user_full_details')
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('agency-details/<str:agency_id>/', 
                 self.admin_site.admin_view(self.agency_details_view),
                 name='agency_balance_details'),
        ]
        return custom_urls + urls
    
    def agency_details_view(self, request, agency_id):
        """Custom view to show complete agency balance details"""
        try:
            # Get user with this agency ID (client_id is on UserProfile, not User)
            profile = UserProfile.objects.get(client_id=agency_id)
            user = profile.user
            
            # Get cash balance wallet
            try:
                wallet = user.cash_balance_wallet
            except:
                wallet = None
            
            # Get all transactions for this agency
            if wallet:
                transactions = CashBalanceTransaction.objects.filter(
                    cash_balance_wallet=wallet
                ).order_by('-created_at')
                
                # Calculate statistics
                total_credits = transactions.filter(amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
                total_debits = abs(transactions.filter(amount__lt=0).aggregate(Sum('amount'))['amount__sum'] or 0)
                total_transactions = transactions.count()
                recharge_count = transactions.filter(transaction_type='recharge').count()
                payment_count = transactions.filter(transaction_type='payment').count()
                refund_count = transactions.filter(transaction_type='refund').count()
            else:
                transactions = []
                total_credits = 0
                total_debits = 0
                total_transactions = 0
                recharge_count = 0
                payment_count = 0
                refund_count = 0
            
            # Get bookings for this user
            bookings = Booking.objects.filter(user=user).order_by('-created_at')[:10]
            
            context = {
                'title': f'Agency Balance Details - {agency_id}',
                'agency_id': agency_id,
                'user': user,
                'profile': profile,
                'wallet': wallet,
                'transactions': transactions,
                'total_credits': total_credits,
                'total_debits': total_debits,
                'total_transactions': total_transactions,
                'recharge_count': recharge_count,
                'payment_count': payment_count,
                'refund_count': refund_count,
                'recent_bookings': bookings,
                'opts': self.model._meta,
                'has_view_permission': self.has_view_permission(request),
            }
            
            return render(request, 'admin/agency_balance_details.html', context)
            
        except User.DoesNotExist:
            messages.error(request, f'Agency with ID {agency_id} not found.')
            return HttpResponseRedirect(reverse('admin:travels_cashbalancetransaction_changelist'))
    
    fieldsets = (
        ('User Information', {
            'fields': ('user_full_details', 'cash_balance_wallet')
        }),
        ('Transaction Information', {
            'fields': ('transaction_type', 'amount', 'balance_after', 'is_credit_display')
        }),
        ('Transaction Details', {
            'fields': ('description', 'reference_id')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def wallet_user(self, obj):
        if obj.cash_balance_wallet and obj.cash_balance_wallet.user:
            user = obj.cash_balance_wallet.user
            if hasattr(user, 'profile'):
                return format_html(
                    '<a href="/admin/travels/userprofile/{}/change/">{}</a>',
                    user.profile.id, user.email
                )
            return user.email
        return 'N/A'
    wallet_user.short_description = 'User Email'
    
    def agency_id_clickable(self, obj):
        if obj.cash_balance_wallet and obj.cash_balance_wallet.user:
            user = obj.cash_balance_wallet.user
            agency_id = getattr(user.profile, 'client_id', None) if hasattr(user, 'profile') else None
            if agency_id:
                # Create a clickable link to agency details page
                url = reverse('admin:agency_balance_details', args=[agency_id])
                return format_html(
                    '<a href="{}" style="font-weight: bold; color: #2563eb; text-decoration: none; padding: 4px 8px; background: #dbeafe; border-radius: 4px; display: inline-block;" target="_blank">📊 {}</a>',
                    url, agency_id
                )
            return 'N/A'
        return 'N/A'
    agency_id_clickable.short_description = 'Agency ID'
    
    def user_full_details(self, obj):
        if obj.cash_balance_wallet and obj.cash_balance_wallet.user:
            user = obj.cash_balance_wallet.user
            profile = getattr(user, 'profile', None)
            details = f"""
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                <h3 style="margin-top: 0;">User Details</h3>
                <p><strong>Email:</strong> {user.email}</p>
                <p><strong>Agency ID:</strong> {profile.client_id if profile else 'N/A'}</p>
                <p><strong>Name:</strong> {profile.full_name if profile else 'N/A'}</p>
                <p><strong>Phone:</strong> {user.phone if user.phone else 'N/A'}</p>
                <p><strong>Current Balance:</strong> ₹{obj.cash_balance_wallet.balance}</p>
                <p><strong>User Type:</strong> {user.get_user_type_display()}</p>
                <p><strong>Approved:</strong> {'Yes' if user.is_approved else 'No'}</p>
            </div>
            """
            return format_html(details)
        return 'N/A'
    user_full_details.short_description = 'Complete User Information'
    
    def description_short(self, obj):
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_short.short_description = 'Description'
    
    def amount_display(self, obj):
        if obj.amount > 0:
            return format_html('<span style="color: green; font-weight: bold; font-size: 14px;">+₹{}</span>', f'{float(obj.amount):.2f}')
        else:
            return format_html('<span style="color: red; font-weight: bold; font-size: 14px;">-₹{}</span>', f'{float(abs(obj.amount)):.2f}')
    amount_display.short_description = 'Amount'
    
    def is_credit_display(self, obj):
        if obj.is_credit:
            return format_html('<span style="background: #10b981; color: white; padding: 3px 8px; border-radius: 3px;">Credit</span>')
        return format_html('<span style="background: #ef4444; color: white; padding: 3px 8px; border-radius: 3px;">Debit</span>')
    is_credit_display.short_description = 'Type'

@admin.register(GroupRequest)
class GroupRequestAdmin(admin.ModelAdmin):
    """Admin interface for Group Booking Requests"""
    list_display = ('reference_id', 'contact_name', 'contact_email', 'origin', 'destination', 
                    'departure_date', 'number_of_passengers', 'status', 'created_at')
    list_filter = ('status', 'trip_type', 'travel_class', 'created_at')
    search_fields = ('reference_id', 'contact_name', 'contact_email', 'contact_phone', 
                     'company_name', 'origin', 'destination')
    readonly_fields = ('reference_id', 'user', 'created_at', 'updated_at')
    fieldsets = (
        ('Request Information', {
            'fields': ('reference_id', 'user', 'status', 'created_at', 'updated_at')
        }),
        ('Contact Information', {
            'fields': ('contact_name', 'contact_email', 'contact_phone', 'company_name')
        }),
        ('Travel Details', {
            'fields': ('origin', 'destination', 'departure_date', 'return_date', 
                      'trip_type', 'travel_class')
        }),
        ('Passenger Details', {
            'fields': ('number_of_passengers', 'adults', 'children', 'infants')
        }),
        ('Additional Information', {
            'fields': ('special_requirements', 'additional_notes', 'estimated_amount')
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',)
        }),
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    def get_readonly_fields(self, request, obj=None):
        """Make reference_id readonly on create, all fields readonly on update"""
        if obj:  # Editing an existing object
            return self.readonly_fields + ('user',)
        return self.readonly_fields

@admin.register(PackageApplication)
class PackageApplicationAdmin(admin.ModelAdmin):
    """Admin interface for Package Applications"""
    list_display = ('package_name', 'destination', 'full_name', 'email', 'phone', 
                    'number_of_people', 'travel_date', 'status', 'created_at')
    list_filter = ('status', 'package_name', 'destination', 'created_at')
    search_fields = ('package_name', 'destination', 'full_name', 'email', 'phone', 
                     'special_requests')
    readonly_fields = ('created_at', 'updated_at', 'ip_address', 'user_agent')
    fieldsets = (
        ('Application Information', {
            'fields': ('package_name', 'destination', 'user', 'status', 'created_at', 'updated_at')
        }),
        ('Contact Information', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Travel Details', {
            'fields': ('travel_date', 'number_of_people', 'special_requests')
        }),
        ('Financial Information', {
            'fields': ('estimated_amount',)
        }),
        ('Admin Notes', {
            'fields': ('admin_notes',)
        }),
        ('System Information', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    actions = ['mark_as_contacted', 'mark_as_processing', 'mark_as_confirmed', 'mark_as_cancelled']
    
    def mark_as_contacted(self, request, queryset):
        queryset.update(status=PackageApplication.Status.CONTACTED)
        self.message_user(request, f'{queryset.count()} application(s) marked as contacted.')
    mark_as_contacted.short_description = 'Mark selected as contacted'
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status=PackageApplication.Status.PROCESSING)
        self.message_user(request, f'{queryset.count()} application(s) marked as processing.')
    mark_as_processing.short_description = 'Mark selected as processing'
    
    def mark_as_confirmed(self, request, queryset):
        queryset.update(status=PackageApplication.Status.CONFIRMED)
        self.message_user(request, f'{queryset.count()} application(s) marked as confirmed.')
    mark_as_confirmed.short_description = 'Mark selected as confirmed'
    
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status=PackageApplication.Status.CANCELLED)
        self.message_user(request, f'{queryset.count()} application(s) marked as cancelled.')
    mark_as_cancelled.short_description = 'Mark selected as cancelled'

@admin.register(SalesRepresentative)
class SalesRepresentativeAdmin(admin.ModelAdmin):
    """Admin interface for Sales Representatives"""
    list_display = ('name', 'phone', 'is_active', 'display_order', 'assigned_users_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'phone')
    list_editable = ('is_active', 'display_order', 'phone')
    fieldsets = (
        ('Sales Representative Information', {
            'fields': ('name', 'phone')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_order'),
            'description': 'Active sales representatives will be shown to their assigned users. Display order determines the sequence.'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('display_order', 'name')
    
    actions = ['activate_sales_reps', 'deactivate_sales_reps']
    
    def assigned_users_count(self, obj):
        return obj.assigned_agencies.count()
    assigned_users_count.short_description = 'Assigned Agencies'
    
    def activate_sales_reps(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} sales representative(s) activated.')
    activate_sales_reps.short_description = 'Activate selected sales representatives'
    
    def deactivate_sales_reps(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} sales representative(s) deactivated.')
    deactivate_sales_reps.short_description = 'Deactivate selected sales representatives'

@admin.register(Umrah)
class UmrahAdmin(admin.ModelAdmin):
    """Admin interface for Umrah applications"""
    list_display = ('reference_id', 'full_name', 'email', 'phone', 'duration', 'preferred_date', 'number_of_passengers', 'status', 'created_at')
    list_filter = ('status', 'duration', 'created_at', 'preferred_date')
    search_fields = ('reference_id', 'full_name', 'email', 'phone')
    readonly_fields = ('reference_id', 'created_at', 'updated_at')
    fieldsets = (
        ('Reference Information', {
            'fields': ('reference_id',)
        }),
        ('Personal Information', {
            'fields': ('full_name', 'email', 'phone', 'passport_size_photo')
        }),
        ('Umrah Details', {
            'fields': ('duration', 'preferred_date', 'number_of_passengers')
        }),
        ('Additional Information', {
            'fields': ('special_requests',)
        }),
        ('Status & Admin Notes', {
            'fields': ('status', 'notes')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    actions = ['mark_as_contacted', 'mark_as_confirmed', 'mark_as_cancelled']
    
    def mark_as_contacted(self, request, queryset):
        queryset.update(status=Umrah.StatusChoices.CONTACTED)
        self.message_user(request, f'{queryset.count()} application(s) marked as contacted.')
    mark_as_contacted.short_description = 'Mark selected as contacted'
    
    def mark_as_confirmed(self, request, queryset):
        queryset.update(status=Umrah.StatusChoices.CONFIRMED)
        self.message_user(request, f'{queryset.count()} application(s) marked as confirmed.')
    mark_as_confirmed.short_description = 'Mark selected as confirmed'
    
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status=Umrah.StatusChoices.CANCELLED)
        self.message_user(request, f'{queryset.count()} application(s) marked as cancelled.')
    mark_as_cancelled.short_description = 'Mark selected as cancelled'

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """Admin interface for Coupon Management"""
    list_display = ('code', 'discount_type', 'discount_value_display', 'min_purchase', 'max_discount', 'valid_from', 'valid_to', 'is_active', 'usage_limit', 'used_count', 'usage_percentage')
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_to')
    search_fields = ('code', 'description')
    readonly_fields = ('used_count', 'created_at', 'updated_at', 'usage_percentage_display')
    date_hierarchy = 'valid_from'
    
    fieldsets = (
        ('Coupon Information', {
            'fields': ('code', 'description', 'is_active')
        }),
        ('Discount Settings', {
            'fields': ('discount_type', 'discount_value', 'min_purchase', 'max_discount'),
            'description': 'Percentage: Enter 0-100. Fixed: Enter amount in INR. Max discount applies only to percentage coupons.'
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_to')
        }),
        ('Usage Limits', {
            'fields': ('usage_limit', 'used_count', 'usage_percentage_display'),
            'description': 'Leave usage limit blank for unlimited uses'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def discount_value_display(self, obj):
        if obj.discount_type == 'percentage':
            return f"{obj.discount_value}%"
        return f"₹{obj.discount_value}"
    discount_value_display.short_description = 'Discount'
    
    def usage_percentage(self, obj):
        if obj.usage_limit:
            return f"{(obj.used_count / obj.usage_limit * 100):.1f}%"
        return "Unlimited"
    usage_percentage.short_description = 'Usage'
    
    def usage_percentage_display(self, obj):
        if obj.usage_limit:
            percentage = (obj.used_count / obj.usage_limit * 100)
            color = 'green' if percentage < 80 else 'orange' if percentage < 95 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}% ({}/{} uses)</span>',
                color, percentage, obj.used_count, obj.usage_limit
            )
        return format_html('<span style="color: green;">Unlimited ({})</span>', obj.used_count)
    usage_percentage_display.short_description = 'Usage Status'
    
    actions = ['activate_coupons', 'deactivate_coupons', 'reset_usage_count']
    
    def activate_coupons(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} coupon(s) activated.")
    activate_coupons.short_description = "Activate selected coupons"
    
    def deactivate_coupons(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} coupon(s) deactivated.")
    deactivate_coupons.short_description = "Deactivate selected coupons"
    
    def reset_usage_count(self, request, queryset):
        updated = queryset.update(used_count=0)
        self.message_user(request, f"Usage count reset for {updated} coupon(s).")
    reset_usage_count.short_description = "Reset usage count for selected coupons"


@admin.register(VisaBooking)
class VisaBookingAdmin(admin.ModelAdmin):
    """Admin interface for managing Visa Bookings/Applications"""
    list_display = (
        'reference_id', 'full_name', 'country_display', 'duration', 
        'price_display', 'status_badge', 'payment_status_badge', 
        'travel_date', 'created_at'
    )
    list_filter = ('country', 'status', 'payment_status', 'created_at', 'travel_date')
    search_fields = ('reference_id', 'full_name', 'email', 'phone', 'passport_number')
    ordering = ('-created_at',)
    readonly_fields = ('reference_id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Application Info', {
            'fields': ('reference_id', 'user', 'status', 'payment_status', 'payment_id')
        }),
        ('Applicant Details', {
            'fields': ('full_name', 'email', 'phone', 'passport_number', 'nationality', 'address')
        }),
        ('Visa Details', {
            'fields': ('country', 'duration', 'visa_type', 'travel_date', 'price', 'currency')
        }),
        ('Documents', {
            'fields': ('passport_front', 'passport_back', 'passport_size_photo'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def country_display(self, obj):
        return f"{obj.get_country_flag()} {obj.get_country_display()}"
    country_display.short_description = 'Country'
    country_display.admin_order_field = 'country'
    
    def price_display(self, obj):
        return f"₹{obj.price:,.2f}"
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'processing': '#3498db',
            'approved': '#27ae60',
            'rejected': '#e74c3c',
            'completed': '#2ecc71',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def payment_status_badge(self, obj):
        colors = {
            'pending': '#f39c12',
            'paid': '#27ae60',
            'failed': '#e74c3c',
            'refunded': '#9b59b6',
        }
        color = colors.get(obj.payment_status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 10px; font-size: 11px;">{}</span>',
            color, obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Payment'
    payment_status_badge.admin_order_field = 'payment_status'
    
    actions = ['mark_as_processing', 'mark_as_approved', 'mark_as_rejected', 'mark_as_paid', 'mark_as_refunded']
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f"{updated} application(s) marked as Processing.")
    mark_as_processing.short_description = "Mark selected as Processing"
    
    def mark_as_approved(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f"{updated} application(s) marked as Approved.")
    mark_as_approved.short_description = "Mark selected as Approved"
    
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f"{updated} application(s) marked as Rejected.")
    mark_as_rejected.short_description = "Mark selected as Rejected"
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(payment_status='paid')
        self.message_user(request, f"{updated} application(s) marked as Paid.")
    mark_as_paid.short_description = "Mark payment as Paid"
    
    def mark_as_refunded(self, request, queryset):
        updated = queryset.update(payment_status='refunded')
        self.message_user(request, f"{updated} application(s) marked as Refunded.")
    mark_as_refunded.short_description = "Mark payment as Refunded"


@admin.register(BookingChangeRequest)
class BookingChangeRequestAdmin(admin.ModelAdmin):
    """Admin interface for managing booking change requests"""
    list_display = ('reference_number', 'booking_ref', 'request_type', 'user_email', 'status', 'created_at', 'processed_at')
    list_filter = ('status', 'request_type', 'created_at')
    search_fields = ('reference_number', 'booking__booking_reference', 'user__email', 'requested_value')
    readonly_fields = ('reference_number', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Request Details', {
            'fields': ('reference_number', 'booking', 'user', 'request_type', 'status')
        }),
        ('Change Information', {
            'fields': ('current_value', 'requested_value', 'reason')
        }),
        ('Admin Response', {
            'fields': ('admin_notes', 'processed_by', 'processed_at', 'change_fee')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def booking_ref(self, obj):
        return obj.booking.booking_reference
    booking_ref.short_description = 'Booking Ref'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Requested By'
    
    actions = ['mark_as_processing', 'mark_as_approved', 'mark_as_rejected', 'mark_as_completed']
    
    def mark_as_processing(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='processing', processed_by=request.user, processed_at=timezone.now())
        self.message_user(request, f"{updated} request(s) marked as Processing.")
    mark_as_processing.short_description = "Mark as Processing"
    
    def mark_as_approved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='approved', processed_by=request.user, processed_at=timezone.now())
        self.message_user(request, f"{updated} request(s) marked as Approved.")
    mark_as_approved.short_description = "Mark as Approved"
    
    def mark_as_rejected(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='rejected', processed_by=request.user, processed_at=timezone.now())
        self.message_user(request, f"{updated} request(s) marked as Rejected.")
    mark_as_rejected.short_description = "Mark as Rejected"
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='completed', processed_by=request.user, processed_at=timezone.now())
        self.message_user(request, f"{updated} request(s) marked as Completed.")
    mark_as_completed.short_description = "Mark as Completed"

