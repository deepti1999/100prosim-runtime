from django import template

register = template.Library()

@register.filter
def format_energy(value):
    """
    Format energy values for display in bilanz table.
    - Hides zeros (returns empty string)
    - Formats numbers with German thousand separators (dot, per
      stakeholder PDF §2.5.2) and no decimals.
    """
    try:
        num = float(value)
        if num == 0 or num == 0.0:
            return ""
        # Build English-comma form first, then swap to German dot grouping.
        return f"{int(round(num)):,}".replace(",", ".")
    except (ValueError, TypeError):
        return ""

@register.filter
def not_zero(value):
    """Check if value is not zero"""
    try:
        return float(value) != 0
    except (ValueError, TypeError):
        return False
