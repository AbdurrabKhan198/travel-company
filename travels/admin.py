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
    Package, PackageImage, Contact, Wallet, WalletTransaction
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
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    inlines = (UserProfileInline,)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'user_type'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
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
    list_display = ('user', 'full_name', 'aadhar_number', 'id_type', 'city', 'country', 'date_of_birth', 'has_pdfs')
    search_fields = ('user__email', 'full_name', 'aadhar_number', 'id_number', 'city', 'country')
    list_filter = ('gender', 'country', 'city', 'id_type')
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'full_name', 'date_of_birth', 'gender', 'profile_picture')
        }),
        ('Contact Information', {
            'fields': ('address', 'city', 'state', 'country', 'pincode')
        }),
        ('Identification', {
            'fields': ('aadhar_number', 'id_type', 'id_number'),
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
    fields = ('departure_date', 'arrival_date', 'total_seats', 'available_seats', 'price', 'is_active', 'notes')

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

class BookingPassengerInline(admin.TabularInline):
    model = BookingPassenger
    extra = 0
    readonly_fields = ('full_name', 'age', 'passenger_type')
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

class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = ('transaction_type', 'amount', 'balance_after', 'description', 'reference_id', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj):
        return False

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'balance', 'is_active', 'max_balance', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'user_email', 'transaction_count')
    inlines = [WalletTransactionInline]
    date_hierarchy = 'created_at'
    actions = ['activate_wallets', 'deactivate_wallets']
    
    fieldsets = (
        ('Wallet Information', {
            'fields': ('user_email', 'balance', 'max_balance', 'is_active')
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
        self.message_user(request, f"{updated} wallet(s) activated.")
    activate_wallets.short_description = "Activate selected wallets"
    
    def deactivate_wallets(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} wallet(s) deactivated.")
    deactivate_wallets.short_description = "Deactivate selected wallets"

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet_user', 'transaction_type', 'amount_display', 'balance_after', 'reference_id', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('wallet__user__email', 'description', 'reference_id')
    readonly_fields = ('wallet', 'transaction_type', 'amount', 'balance_after', 'description', 'reference_id', 'created_at', 'updated_at', 'is_credit_display')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('wallet', 'transaction_type', 'amount', 'balance_after', 'is_credit_display')
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
        return obj.wallet.user.email if obj.wallet and obj.wallet.user else 'N/A'
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

