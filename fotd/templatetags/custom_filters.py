import datetime
import re

from django import template
from django.utils.safestring import mark_safe
from django.utils.timesince import timesince

register = template.Library()


@register.filter
def replace(value, args):
    old_value, new_value = args.split(",")
    return value.replace(old_value, new_value)


@register.filter
def startswith(text, starts):
    if isinstance(text, str):
        return text.startswith(starts)
    return False


@register.filter
def keyvalue(dict, key):
    """Get dict value when dict key is a variable"""
    return dict.get(key, "")


@register.filter
def get_previous_end_fb(endfb_changed_items, key):
    return (
        endfb_changed_items.get(key, {}).get("previous", "blank")
        if endfb_changed_items
        else "blank"
    )


@register.filter
def roughtime_since(value):
    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        value = datetime.datetime.combine(value, datetime.datetime.min.time())
    elif not isinstance(value, datetime.datetime):
        # print(f'Not a datetime: {value}, it is of type {type(value)}')
        return "Unknown"

    time_diff = timesince(value)
    # print(f'time_diff: {time_diff} ->{time_diff.split(",")[0]}')

    if value.date() == datetime.datetime.now().date():
        return "today"
    else:
        # only keep the first time unit (day, week etc.) and remove the rest
        return time_diff.split(",")[0] + " ago"


@register.filter
def linkify(str):
    """
    Convert a plain text into html with links for matching patterns

    Long URL will be truncated when using as anchor text
    Any PR number, feature numbers, or Outlook names within an anchor text
    shouldn't be further transformed to break the link
    """

    # pattern to match normal URL and also a truncated URL with '...' in the middle
    url_pattern = re.compile(
        r"https?://[^\s.]+(?:\.[^\s.]+)*(?:/[^\s]*)?(?:\.\.\.[^\s]*)?"
    )

    # patterns and the target html link to be replaced with
    non_url_patterns = {
        r"PR\d{6}": "https://pronto.ext.net.nokia.com/pronto/problemReportSearch.html?freeTextdropDownID=prId&searchTopText={}",  # NOQA
        r"CB\d{6}-[CS]R": "/backlog/{}/",
        r"CB\d{4,6}": "/backlog/{}/",
        r"CNI-\d{6}": "/backlog/{}/",
        # outlook display name in the form of 'Firstname Lastname (Nokia|NSB)',
        # may have a number and middle name in between
        r"\b[A-Z][a-z]+(?:-[A-Z][a-z]+)?(?: [A-Z]\.)?(?: \d{1,2}\.)? [A-Z][a-z]+ \((Nokia|NSB)\)": "copy-to-clipboard:{}",  # NOQA
    }

    def linkify_matches(match):
        for pattern, url in non_url_patterns.items():
            if re.fullmatch(pattern, match.group(0)):
                if "copy-to-clipboard" in url:
                    name = match.group(0)
                    return (
                        f'<a href="#copy-to-clipboard" '
                        f"onclick=\"navigator.clipboard.writeText('{name}'); "
                        f"alert('Name copied: {name}'); return false;\">{name}</a>"
                    )
                else:
                    # complement the feature number with 0s if it's incomplete
                    if pattern == r"CB\d{4,6}":
                        cb_number = match.group(0)
                        cb_number_padded = (
                            cb_number[:2] + cb_number[2:].zfill(6) + "-SR"
                        )
                        return (
                            f'<a href="{url.format(cb_number_padded)}" '
                            f'target="_blank">{cb_number}</a>'
                        )

                    return (
                        f'<a href="{url.format(match.group(0))}" '
                        f'target="_blank">{match.group(0)}</a>'
                    )
        return match.group(0)

    def linkify_per_patterns(match):
        """Skip if it's a URL (or a truncated URL) to avoid further transformation"""
        if url_pattern.search(match.group(0)):
            # print(f'Matched URL: {match.group(0)}')
            return match.group(0)

        return linkify_matches(match)

    def truncate_url_as_anchor(match):
        url = match.group(0)
        if len(url) > 50:
            return f"{url[:20]}...{url[-20:]}"  # Truncate
        return url

    # convert URLs in the string into html links, and truncate long url as anchor text
    urlized_str = url_pattern.sub(
        lambda match: (
            f'<a href="{match.group(0)}" target="_blank">'
            f"{truncate_url_as_anchor(match)}</a>"
        ),
        str,
    )
    # print(f'urlized_str: {urlized_str}')

    # Then, handle PR/feature numbers or names, but skip already processed URLs
    combined_patterns = "|".join(f"({pattern})" for pattern in non_url_patterns.keys())
    combined_patterns = f"({url_pattern.pattern})|{combined_patterns}"
    regex = re.compile(combined_patterns)
    result = regex.sub(linkify_per_patterns, urlized_str)

    return mark_safe(result)
