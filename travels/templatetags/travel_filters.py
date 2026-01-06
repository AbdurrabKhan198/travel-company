from django import template
import math

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    return dictionary.get(key, '')

@register.filter
def multiply(value, arg):
    """Multiply the value by the arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        try:
            return value * int(arg)
        except (ValueError, TypeError):
            return ''

@register.filter
def duration_format(minutes):
    """Format duration in minutes to 'Xh Ym' format"""
    try:
        minutes = int(minutes)
        hours = minutes // 60
        mins = minutes % 60
        
        if hours > 0 and mins > 0:
            return f"{hours}h {mins}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{mins}m"
    except (ValueError, TypeError):
        return str(minutes)

@register.filter
def passenger_type_count(queryset, passenger_type):
    """Count passengers of a specific type in a queryset"""
    try:
        return queryset.filter(passenger_type=passenger_type).count()
    except (AttributeError, TypeError):
        return 0

@register.filter
def abs_value(value):
    """Return absolute value of a number"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0


@register.filter
def airline_logo(carrier_code):
    """Return airline logo URL based on carrier code (CDN fallback)"""
    if not carrier_code:
        return ''
    
    # Extract airline code (first 2 characters)
    code = str(carrier_code).strip().upper()[:2]
    
    # Return CDN URL - fallback if static not found
    return f'https://pics.avs.io/200/80/{code}.png'


@register.filter
def airline_logo_static(airline_name):
    """Return static file path for airline logo based on airline name from database.
    The logo files should be in static/images/flight-logo/{airline_name}.png
    E.g., "Air India" -> "/static/images/flight-logo/air-india.png"
    """
    if not airline_name:
        return ''
    
    # Convert to lowercase and replace spaces with hyphens for file path
    name = str(airline_name).strip().lower().replace(' ', '-')
    return f'/static/images/flight-logo/{name}.png'


@register.filter
def airline_name_from_code(carrier_code):
    """Return airline name based on carrier code"""
    if not carrier_code:
        return 'Airline'
    
    code = str(carrier_code).strip().upper()[:2]
    
    airline_names = {
        '6E': 'IndiGo',
        'AI': 'Air India',
        'UK': 'Vistara',
        'SG': 'SpiceJet',
        'G8': 'Go First',
        'I5': 'AirAsia India',
        'IX': 'Air India Express',
        'QP': 'Akasa Air',
        '9I': 'Alliance Air',
        'S5': 'Star Air',
        'EK': 'Emirates',
        'EY': 'Etihad Airways',
        'QR': 'Qatar Airways',
        'SQ': 'Singapore Airlines',
        'TG': 'Thai Airways',
        'MH': 'Malaysia Airlines',
        'CX': 'Cathay Pacific',
        'BA': 'British Airways',
        'LH': 'Lufthansa',
        'AF': 'Air France',
        'KL': 'KLM',
        'TK': 'Turkish Airlines',
        'SV': 'Saudia',
        'GF': 'Gulf Air',
        'WY': 'Oman Air',
        'FZ': 'Fly Dubai',
        'G9': 'Air Arabia',
        'UL': 'SriLankan Airlines',
        'BG': 'Biman Bangladesh',
        'PK': 'Pakistan International',
        'RA': 'Nepal Airlines',
    }
    
    return airline_names.get(code, 'Airline')