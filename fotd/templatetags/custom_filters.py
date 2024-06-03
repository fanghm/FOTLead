from django import template

register = template.Library()

@register.filter
def replace(value, args):
    old_value, new_value = args.split(',')
    return value.replace(old_value, new_value)
    
@register.filter
def startswith(text, starts):
    if isinstance(text, str):
        return text.startswith(starts)
    return False