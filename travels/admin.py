from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.contrib import messages

from .models import (
    User, UserProfile, Route, Schedule, Booking, BookingPassenger,
    Package, PackageImage, Contact, ODWallet, ODWalletTransaction, 
    CashBalanceWallet, CashBalanceTransaction, GroupRequest, PackageApplication, Executive, Umrah, PNRStock
)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    extra = 0
    readonly_fields = ('created_at', 'updated_at')

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'client_id', 'first_name', 'last_name', 'user_type', 'is_approved', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_approved', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'client_id', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('client_id',)
    inlines = (UserProfileInline,)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone', 'client_id')}),
        (_('Account Status'), {
            'fields': ('is_approved', 'is_active', 'is_verified'),
            'description': 'is_approved: User can login only if approved. Account will be reviewed within 24 hours.'
        }),
        (_('Permissions'), {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions', 'user_type'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    actions = ['approve_users', 'unapprove_users']
    
    def approve_users(self, request, queryset):
        """Approve selected users and send approval emails"""
        count = 0
        for user in queryset:
            if not user.is_approved:
                user.is_approved = True
                user.save()  # This will trigger the signal to send approval email
                count += 1
        self.message_user(request, f'{count} user(s) approved successfully. Approval emails have been sent.')
    approve_users.short_description = 'Approve selected users'
    
    def unapprove_users(self, request, queryset):
        """Unapprove selected users"""
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} user(s) unapproved.')
    unapprove_users.short_description = 'Unapprove selected users'
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type'),
        }),
    )
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'title', 'gst_number', 'id_type', 'city', 'country', 'date_of_birth', 'has_pdfs')
    search_fields = ('user__email', 'full_name', 'gst_number', 'id_number', 'city', 'country')
    list_filter = ('gender', 'country', 'city', 'id_type', 'title')
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'title', 'full_name', 'date_of_birth', 'gender', 'profile_picture')
        }),
        ('Contact Information', {
            'fields': ('address', 'city', 'state', 'country', 'pincode')
        }),
        ('Company Information', {
            'fields': ('company_name', 'gst_number'),
            'classes': ('collapse',)
        }),
        ('Identification', {
            'fields': ('id_type', 'id_number'),
            'classes': ('collapse',)
        }),
        ('PDF Documents', {
            'fields': ('id_document_pdf', 'passport_pdf', 'other_documents'),
            'classes': ('collapse',),
            'description': 'User uploaded PDF documents'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'profile_picture_preview', 'has_pdfs')
    
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
    fields = ('departure_date', 'arrival_date', 'total_seats', 'available_seats', 'price', 'adult_fare', 'child_fare', 'infant_fare', 'is_active', 'notes')

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'from_location', 'to_location', 'transport_type', 'duration_formatted', 'base_price', 'is_non_refundable', 'is_active')
    list_filter = ('transport_type', 'route_type', 'is_active', 'is_non_refundable')
    search_fields = ('name', 'from_location', 'to_location', 'carrier_number')
    inlines = [ScheduleInline]
    readonly_fields = ('created_at', 'updated_at', 'duration_formatted')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'from_location', 'to_location', 'transport_type', 'carrier_number', 'route_type')
        }),
        ('Schedule', {
            'fields': ('departure_time', 'arrival_time', 'duration')
        }),
        ('Terminal Information', {
            'fields': ('departure_terminal', 'arrival_terminal')
        }),
        ('Pricing & Status', {
            'fields': ('base_price', 'is_non_refundable', 'is_active')
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

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('route', 'departure_date', 'arrival_date', 'price', 'adult_fare', 'child_fare', 'infant_fare', 'available_seats', 'total_seats', 'is_active')
    list_filter = ('is_active', 'departure_date', 'route__transport_type')
    search_fields = ('route__name', 'route__from_location', 'route__to_location', 'route__carrier_number')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'departure_date'
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('route', 'departure_date', 'arrival_date', 'is_active')
        }),
        ('Seating', {
            'fields': ('total_seats', 'available_seats')
        }),
        ('Pricing', {
            'fields': ('price', 'adult_fare', 'child_fare', 'infant_fare'),
            'description': 'Base price is used as default adult fare if adult_fare is not set. Child and infant fares are typically around ₹4000.'
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

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

class PackageImageInline(admin.TabularInline):
    model = PackageImage
    extra = 1
    readonly_fields = ('preview_image',)
    
    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return "No image"
    preview_image.short_description = 'Preview'

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('title', 'destination', 'package_type', 'duration_display', 'base_price', 'discounted_price', 'is_featured', 'is_active')
    list_filter = ('package_type', 'is_featured', 'is_active')
    search_fields = ('title', 'destination', 'short_description')
    prepopulated_fields = {'slug': ('title', 'destination')}
    inlines = [PackageImageInline]
    readonly_fields = ('created_at', 'updated_at', 'meta_preview')
    save_on_top = True
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'destination', 'package_type', 'is_featured', 'is_active')
        }),
        ('Pricing', {
            'fields': ('base_price', 'discount_percentage', 'discounted_price')
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

@admin.register(PackageImage)
class PackageImageAdmin(admin.ModelAdmin):
    list_display = ('package', 'preview_image', 'is_primary', 'display_order')
    list_editable = ('is_primary', 'display_order')
    list_filter = ('is_primary', 'package__destination')
    search_fields = ('package__title', 'package__destination')
    
    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.image.url
            )
        return "No image"
    preview_image.short_description = 'Preview'

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
    list_display = ('user_email', 'balance', 'is_active', 'max_balance', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'user_email', 'transaction_count')
    inlines = [ODWalletTransactionInline]
    date_hierarchy = 'created_at'
    actions = ['activate_wallets', 'deactivate_wallets', 'recharge_wallets']
    
    fieldsets = (
        ('OD Wallet Information', {
            'fields': ('user_email', 'balance', 'max_balance', 'is_active'),
            'description': 'OD Wallet can only be recharged by admin. Users can only use it when active.'
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
        if obj.amount > 0:
            return format_html('<span style="color: green;">+₹{}</span>', obj.amount)
        else:
            return format_html('<span style="color: red;">-₹{}</span>', abs(obj.amount))
    amount_display.short_description = 'Amount'
    
    def is_credit_display(self, obj):
        return "Credit" if obj.is_credit else "Debit"
    is_credit_display.short_description = 'Type'

class CashBalanceTransactionInline(admin.TabularInline):
    model = CashBalanceTransaction
    extra = 0
    readonly_fields = ('transaction_type', 'amount', 'balance_after', 'description', 'reference_id', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj):
        return False

@admin.register(CashBalanceWallet)
class CashBalanceWalletAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'balance', 'max_balance', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'user_email', 'transaction_count')
    inlines = [CashBalanceTransactionInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Cash Balance Wallet Information', {
            'fields': ('user_email', 'balance', 'max_balance'),
            'description': 'Cash Balance Wallet - Users can recharge themselves. Direct access for everyone.'
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
    
    def transaction_count(self, obj):
        return obj.transactions.count()
    transaction_count.short_description = 'Total Transactions'

@admin.register(CashBalanceTransaction)
class CashBalanceTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet_user', 'transaction_type', 'amount_display', 'balance_after', 'reference_id', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('cash_balance_wallet__user__email', 'description', 'reference_id')
    readonly_fields = ('cash_balance_wallet', 'transaction_type', 'amount', 'balance_after', 'description', 'reference_id', 'created_at', 'updated_at', 'is_credit_display')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('cash_balance_wallet', 'transaction_type', 'amount', 'balance_after', 'is_credit_display')
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
        return obj.cash_balance_wallet.user.email if obj.cash_balance_wallet and obj.cash_balance_wallet.user else 'N/A'
    wallet_user.short_description = 'User'
    
    def amount_display(self, obj):
        if obj.amount > 0:
            return format_html('<span style="color: green;">+₹{}</span>', obj.amount)
        else:
            return format_html('<span style="color: red;">-₹{}</span>', abs(obj.amount))
    amount_display.short_description = 'Amount'
    
    def is_credit_display(self, obj):
        return "Credit" if obj.is_credit else "Debit"
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

@admin.register(Executive)
class ExecutiveAdmin(admin.ModelAdmin):
    """Admin interface for Executives"""
    list_display = ('name', 'phone', 'city', 'is_active', 'display_order', 'created_at')
    list_filter = ('is_active', 'city', 'created_at')
    search_fields = ('name', 'phone', 'city')
    list_editable = ('is_active', 'display_order', 'phone')
    fieldsets = (
        ('Executive Information', {
            'fields': ('name', 'phone', 'city')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_order'),
            'description': 'Active executives will be shown in the header. Display order determines the sequence.'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('display_order', 'name')
    
    actions = ['activate_executives', 'deactivate_executives']
    
    def activate_executives(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} executive(s) activated.')
    activate_executives.short_description = 'Activate selected executives'
    
    def deactivate_executives(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} executive(s) deactivated.')
    deactivate_executives.short_description = 'Deactivate selected executives'

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
            'fields': ('full_name', 'email', 'phone')
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

@admin.register(PNRStock)
class PNRStockAdmin(admin.ModelAdmin):
    """Admin interface for PNR Stock Management - Route-specific PNRs"""
    list_display = ('pnr', 'route_info', 'is_assigned', 'assigned_to_passenger', 'assigned_at', 'created_at')
    list_filter = ('is_assigned', 'route', 'created_at', 'assigned_at')
    search_fields = ('pnr', 'route__from_location', 'route__to_location', 'route__carrier_number', 
                     'assigned_to__first_name', 'assigned_to__last_name', 'assigned_to__booking__booking_reference')
    readonly_fields = ('assigned_to', 'assigned_at', 'created_at', 'updated_at')
    fieldsets = (
        ('PNR Information', {
            'fields': ('pnr', 'route', 'is_assigned'),
            'description': 'PNR is route-specific. Each route has its own pool of PNRs.'
        }),
        ('Assignment Information', {
            'fields': ('assigned_to', 'assigned_at'),
            'description': 'Shows which passenger this PNR is assigned to (if assigned)'
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ('route', '-created_at')
    date_hierarchy = 'created_at'
    
    def route_info(self, obj):
        if obj.route:
            return f"{obj.route.from_location} → {obj.route.to_location} ({obj.route.carrier_number})"
        return "No Route"
    route_info.short_description = 'Route'
    
    def assigned_to_passenger(self, obj):
        if obj.assigned_to:
            booking_ref = obj.assigned_to.booking.booking_reference if obj.assigned_to.booking else 'N/A'
            return f"{obj.assigned_to.full_name} (Booking: {booking_ref})"
        return "Not assigned"
    assigned_to_passenger.short_description = 'Assigned To'
    
    actions = ['bulk_add_pnrs']
    
    def bulk_add_pnrs(self, request, queryset):
        """Bulk add PNRs - This is a placeholder action"""
        self.message_user(request, "To add PNRs in bulk, use the management command: python manage.py add_pnr_stock --route <route_id> --generate <count>")
    bulk_add_pnrs.short_description = "Bulk add PNRs (use management command)"

