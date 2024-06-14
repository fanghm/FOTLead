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

# when dict key is a variable: https://stackoverflow.com/questions/2894365/use-variable-as-dictionary-key-in-django-template
@register.filter
def keyvalue(dict, key):
    return dict.get(key, '')
