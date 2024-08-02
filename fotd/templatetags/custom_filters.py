import re
from django import template
from django.utils.safestring import mark_safe

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

@register.filter
def get_previous_end_fb(endfb_changed_items, key):
    return endfb_changed_items.get(key, {}).get('previous', 'blank') if endfb_changed_items else 'blank'

# add link to PRs, CB features, CNI features, and email addresses
link_patterns = {
    r'PR\d{6}': 'https://pronto.ext.net.nokia.com/pronto/problemReportSearch.html?freeTextdropDownID=prId&searchTopText={}',
    r'CB\d{6}-[CS]R': '/backlog/{}/',
    # r'CB\d{4,6}': '/backlog/{}-SR/',
    r'CNI-\d{6}': '/backlog/{}/',
    r'\b[A-Z][\w-]+\s(?:[\w-]+\s)*(?:\d{1,2}\.\s)?\w+\s\((Nokia|NSB)\)': 'copy-to-clipboard:{}',
}

@register.filter
def linkify(value):
    def replace_match(match):
        for pattern, url in link_patterns.items():
            if re.fullmatch(pattern, match.group(0)):
                if 'copy-to-clipboard' in url:
                    name = match.group(0)
                    return f'<a href="#" onclick="navigator.clipboard.writeText(\'{name}\'); alert(\'Copied: {name}\'); return false;">{name}</a>'
                else:
                    return f'<a href="{url.format(match.group(0))}" target="_blank">{match.group(0)}</a>'
        return match.group(0)

    combined_pattern = '|'.join(f'({pattern})' for pattern in link_patterns.keys())
    regex = re.compile(combined_pattern)
    result = regex.sub(replace_match, value)
    return mark_safe(result)