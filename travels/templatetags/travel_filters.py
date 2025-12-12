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