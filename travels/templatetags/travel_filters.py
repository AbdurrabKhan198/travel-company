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
    """Return airline logo URL based on carrier code"""
    if not carrier_code:
        return ''
    
    # Extract airline code (first 2 characters)
    code = str(carrier_code).strip().upper()[:2]
    
    # Airline logo mappings - using pics.avs.io CDN
    # Format: https://pics.avs.io/200/80/{IATA_CODE}.png
    airline_logos = {
        # Indian Airlines
        '6E': 'https://pics.avs.io/200/80/6E.png',  # IndiGo
        'AI': 'https://pics.avs.io/200/80/AI.png',  # Air India
        'UK': 'https://pics.avs.io/200/80/UK.png',  # Vistara
        'SG': 'https://pics.avs.io/200/80/SG.png',  # SpiceJet
        'G8': 'https://pics.avs.io/200/80/G8.png',  # Go First
        'I5': 'https://pics.avs.io/200/80/I5.png',  # AirAsia India
        'IX': 'https://pics.avs.io/200/80/IX.png',  # Air India Express
        'QP': 'https://pics.avs.io/200/80/QP.png',  # Akasa Air
        '9I': 'https://pics.avs.io/200/80/9I.png',  # Alliance Air
        'S5': 'https://pics.avs.io/200/80/S5.png',  # Star Air
        
        # International Airlines
        'EK': 'https://pics.avs.io/200/80/EK.png',  # Emirates
        'EY': 'https://pics.avs.io/200/80/EY.png',  # Etihad
        'QR': 'https://pics.avs.io/200/80/QR.png',  # Qatar Airways
        'SQ': 'https://pics.avs.io/200/80/SQ.png',  # Singapore Airlines
        'TG': 'https://pics.avs.io/200/80/TG.png',  # Thai Airways
        'MH': 'https://pics.avs.io/200/80/MH.png',  # Malaysia Airlines
        'CX': 'https://pics.avs.io/200/80/CX.png',  # Cathay Pacific
        'BA': 'https://pics.avs.io/200/80/BA.png',  # British Airways
        'LH': 'https://pics.avs.io/200/80/LH.png',  # Lufthansa
        'AF': 'https://pics.avs.io/200/80/AF.png',  # Air France
        'KL': 'https://pics.avs.io/200/80/KL.png',  # KLM
        'TK': 'https://pics.avs.io/200/80/TK.png',  # Turkish Airlines
        'SV': 'https://pics.avs.io/200/80/SV.png',  # Saudia
        'GF': 'https://pics.avs.io/200/80/GF.png',  # Gulf Air
        'WY': 'https://pics.avs.io/200/80/WY.png',  # Oman Air
        'FZ': 'https://pics.avs.io/200/80/FZ.png',  # Fly Dubai
        'G9': 'https://pics.avs.io/200/80/G9.png',  # Air Arabia
        'UL': 'https://pics.avs.io/200/80/UL.png',  # SriLankan Airlines
        'BG': 'https://pics.avs.io/200/80/BG.png',  # Biman Bangladesh
        'PK': 'https://pics.avs.io/200/80/PK.png',  # PIA
        'RA': 'https://pics.avs.io/200/80/RA.png',  # Nepal Airlines
    }
    
    # Return logo URL or generic aviation icon
    if code in airline_logos:
        return airline_logos[code]
    else:
        # Fallback to CDN with the code (may work for unlisted airlines)
        return f'https://pics.avs.io/200/80/{code}.png'


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