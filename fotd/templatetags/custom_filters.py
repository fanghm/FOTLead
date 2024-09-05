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

# patterns and the target html link to be replaced with
# to add link to PRs, CB features, CNIs, and outlook names, and replace URL as link with truncated text
link_patterns = {
    r'PR\d{6}': 'https://pronto.ext.net.nokia.com/pronto/problemReportSearch.html?freeTextdropDownID=prId&searchTopText={}',
    r'CB\d{6}-[CS]R': '/backlog/{}/',
    r'CB\d{4,6}': '/backlog/{}/',
    r'CNI-\d{6}': '/backlog/{}/',

    # outlook name in the form of 'First-name Lastname (Nokia|NSB)', may have a number and middle name in between
    r'\b[A-Z][a-z]+(?:-[A-Z][a-z]+)?(?: [A-Z]\.)?(?: \d{1,2}\.)? [A-Z][a-z]+ \((Nokia|NSB)\)': 'copy-to-clipboard:{}',
}

# pattern to match normal URL and also a truncated URL with '...' in the middle
url_pattern = re.compile(r'https?://[^\s.]+(?:\.[^\s.]+)*(?:/[^\s]*)?(?:\.\.\.[^\s]*)?')
#url_pattern = re.compile(r'((([A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=\+\$,\w]+@)?[A-Za-z0-9.-]+|(?:www.|[-;:&=\+\$,\w]+@)[A-Za-z0-9.-]+)((?:\/[\+~%\/.\w\-_]*)?\??(?:[-\+=&;%@.\w_]*)#?(?:[\w]*))?)')

# Convert a plain text into html for matching patterns as defined in link_patterns and url_pattern
# For long URL, it'll be truncated as the anchor text
# For any PR/feature number/Outlook name within the anchor text shouldn't be further transformed
@register.filter
def linkify(str):
    def replace_match(match):
        for pattern, url in link_patterns.items():
            if re.fullmatch(pattern, match.group(0)):
                if 'copy-to-clipboard' in url:
                    name = match.group(0)
                    return f'<a href="#copy-to-clipboard" onclick="navigator.clipboard.writeText(\'{name}\'); alert(\'Name copied: {name}\'); return false;">{name}</a>'
                else:
                    if pattern == r'CB\d{4,6}': # complement the feature number with 0s if it's incomplete
                        cb_number = match.group(0)
                        cb_number_padded = cb_number[:2] + cb_number[2:].zfill(6) + '-SR'
                        return f'<a href="{url.format(cb_number_padded)}" target="_blank">{cb_number}</a>'

                    return f'<a href="{url.format(match.group(0))}" target="_blank">{match.group(0)}</a>'
        return match.group(0)

    def truncate_long_url(match):
        url = match.group(0)
        if len(url) > 50:
            return f'{url[:20]}...{url[-20:]}'
        return url

    # First, handle URLs and replace them with truncated links
    urlized_str = url_pattern.sub(lambda match: f'<a href="{match.group(0)}" target="_blank">{truncate_long_url(match)}</a>', str)
    #print(f'urlized_str: {urlized_str}')

    # Then, handle PR/feature numbers or names, but skip already processed URLs
    def replace_non_url(match):
        if url_pattern.search(match.group(0)):
            print(f'Matched URL: {match.group(0)}')
            return match.group(0)  # Skip if it's a URL (or a truncated URL) to avoid further transformation

        return replace_match(match)

    combined_patterns = '|'.join(f'({pattern})' for pattern in link_patterns.keys())
    combined_patterns = f'({url_pattern.pattern})|{combined_patterns}'
    regex = re.compile(combined_patterns)
    result = regex.sub(replace_non_url, urlized_str)
    
    return mark_safe(result)