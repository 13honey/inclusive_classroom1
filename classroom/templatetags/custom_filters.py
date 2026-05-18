from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def abbreviate_name(value):
    parts = str(value or '').split()
    if not parts:
        return ''
    if len(parts) == 1:
        return parts[0]
    first = parts[0]
    initials = ' '.join(f'{part[0]}.' for part in parts[1:] if part)
    return f'{first} {initials}'


@register.filter
def name_initials(value):
    return ''.join(part[0].upper() for part in str(value or '').split() if part)
