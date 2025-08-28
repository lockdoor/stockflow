from django import template

register = template.Library()

@register.filter
def dict_key(d, key):
    """Django template filter for dict access by key."""
    if d is None:
        return None
    return d.get(key)
