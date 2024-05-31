from django import template

register = template.Library()

@register.filter
def replace(value, args):
    old_value, new_value = args.split(',')
    return value.replace(old_value, new_value)
    