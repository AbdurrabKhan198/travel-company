from django.contrib import admin
from .models import Route, Inventory, Booking, Package

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['flight_number', 'from_location', 'to_location', 'route_type', 'duration', 'created_at']
    search_fields = ['flight_number', 'from_location', 'to_location']
    list_filter = ['route_type', 'from_location', 'to_location']

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['route', 'travel_date', 'available_seats', 'total_seats', 'price', 'is_active']
    list_filter = ['is_active', 'travel_date', 'route', 'route__route_type']
    search_fields = ['route__flight_number', 'route__from_location', 'route__to_location']
    date_hierarchy = 'travel_date'
    list_editable = ['is_active', 'price']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_reference', 'user', 'inventory', 'passenger_name', 'status', 'total_amount', 'booked_at']
    list_filter = ['status', 'booked_at', 'inventory__travel_date']
    search_fields = ['booking_reference', 'passenger_name', 'user__username']
    readonly_fields = ['booking_reference', 'booked_at', 'updated_at']
    date_hierarchy = 'booked_at'

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['destination', 'title', 'price', 'duration', 'is_featured', 'created_at']
    list_filter = ['is_featured', 'created_at']
    search_fields = ['destination', 'title', 'description']
    list_editable = ['is_featured']
