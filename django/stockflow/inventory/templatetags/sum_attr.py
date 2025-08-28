from django import template

register = template.Library()

@register.filter
def sum_attr(items, attr):
    """Sum attribute values in a list of dicts or objects."""
    if not items:
        return 0
    total = 0
    for obj in items:
        value = getattr(obj, attr, None)
        if value is None and isinstance(obj, dict):
            value = obj.get(attr, 0)
        if value is not None:
            total += value
    return total
