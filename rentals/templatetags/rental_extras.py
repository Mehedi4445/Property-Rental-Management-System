from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def stars(value):
    """Render a 0-5 rating as five Bootstrap-icon stars."""
    n = round(float(value or 0))
    return mark_safe("".join(
        f'<i class="bi bi-star{"-fill" if i < n else ""}"></i>' for i in range(5)
    ))
