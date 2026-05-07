from django import template

register = template.Library()


@register.filter
def abbreviate_name(value):
    if not value:
        return ''

    parts = str(value).split()
    if len(parts) <= 1:
        return str(value)

    initials = [f'{part[0].upper()}.' for part in parts[:-1] if part]
    return ' '.join(initials + [parts[-1]])
