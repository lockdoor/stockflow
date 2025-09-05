from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def dict_value(dictionary, key):
    """Get value from dictionary using key"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, {})
    return {}

@register.filter
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        if value is None or arg is None:
            return 0
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, AttributeError):
        return 0
