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

# add link to PRs, CB features, CNI features, and email addresses, and replace URL as link with truncated text
link_patterns = {
    r'PR\d{6}': 'https://pronto.ext.net.nokia.com/pronto/problemReportSearch.html?freeTextdropDownID=prId&searchTopText={}',
    r'CB\d{6}-[CS]R': '/backlog/{}/',
    r'CB\d{4,6}': '/backlog/{}/',
    r'CNI-\d{6}': '/backlog/{}/',
    #r'\b[A-Z][a-z-]+\s(?:[A-Z][\w\.]+\s)?(?:\d{1,2}\.\s)?[A-Z]\w+\s\((Nokia|NSB)\)': 'copy-to-clipboard:{}', 
    # outlook name in the form of 'First-name M. Lastname (Nokia|NSB)'
    r'\b[A-Z][a-z]+(?:-[A-Z][a-z]+)?(?: [A-Z]\.)?(?: \d{1,2}\.)? [A-Z][a-z]+ \((Nokia|NSB)\)': 'copy-to-clipboard:{}',
}

# to match a URL and also a truncated URL with '...' in the middle
url_pattern = re.compile(r'https?://[^\s.]+(?:\.[^\s.]+)*(?:/[^\s]*)?(?:\.\.\.[^\s]*)?')

# URL text (http//....) to be converted as html link and the anchor text to be shown as truncated text if it's too long, 
# while any PR/feature number within the anchor text shouldn't be further transformed
@register.filter
def linkify(value):
    def replace_match(match):
        for pattern, url in link_patterns.items():
            if re.fullmatch(pattern, match.group(0)):
                if 'copy-to-clipboard' in url:
                    name = match.group(0)
                    return f'<a href="#copy-to-clipboard" onclick="navigator.clipboard.writeText(\'{name}\'); alert(\'Name copied: {name}\'); return false;">{name}</a>'
                else:
                    if pattern == r'CB\d{4,6}':
                        cb_number = match.group(0)
                        cb_number_padded = cb_number[:2] + cb_number[2:].zfill(6) + '-SR'
                        return f'<a href="{url.format(cb_number_padded)}" target="_blank">{cb_number}</a>'
                    return f'<a href="{url.format(match.group(0))}" target="_blank">{match.group(0)}</a>'
        return match.group(0)

    def truncate_url(match):
        url = match.group(0)
        if len(url) > 50:
            return f'{url[:20]}...{url[-20:]}'
        return url

    # First, handle URLs and replace them with truncated links
    result1 = url_pattern.sub(lambda match: f'<a href="{match.group(0)}" target="_blank">{truncate_url(match)}</a>', value)

    # Then, handle PR/feature numbers or names, but skip already processed URLs
    def replace_non_url(match):
        if url_pattern.search(match.group(0)):
            #print(f'{match.group(0)} is a URL')
            return match.group(0)  # Skip if it's a URL (or a truncated URL) to avoid further transformation

        return replace_match(match)

    combined_pattern = '|'.join(f'({pattern})' for pattern in link_patterns.keys())
    combined_pattern = f'({url_pattern.pattern})|{combined_pattern}'
    regex = re.compile(combined_pattern)
    result = regex.sub(replace_non_url, result1)
    
    return mark_safe(result)