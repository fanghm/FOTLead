# globals.py
import datetime
from collections import namedtuple

from django.core.cache import cache

from .models import Sprint

CACHE_TIMEOUT = 3600 * 24  # 24 hours
SprintDates = namedtuple('SprintDates', ['start_date', 'end_date'])


def _query_database_for_fb_dict():
    # print("Querying database for FB data")
    sprints = Sprint.objects.values('fb', 'start_date', 'end_date')
    fb_dict = {
        sprint['fb']: SprintDates(sprint['start_date'], sprint['end_date'])
        for sprint in sprints
    }

    # print(f'FB dict size: {len(fb_dict)}')
    return fb_dict


def _get_fb_dict():
    fb_dict = cache.get('fb_dict')
    if fb_dict is None:
        fb_dict = _query_database_for_fb_dict()
        cache.set('fb_dict', fb_dict, timeout=CACHE_TIMEOUT)

    return fb_dict


def _deduce_fb_date(fb, start=True):
    if not fb.startswith('FB'):
        fb = 'FB' + fb

    year = int('20' + fb[2:4])
    fb_number = int(fb[4:6])

    # FBs start on the first Wednesday of the year
    base_date = datetime.date(year, 1, 1)
    while base_date.weekday() != 2:  # 0 = Monday, 1 = Tuesday, ..., 6 = Sunday
        base_date += datetime.timedelta(days=1)

    days_offset = (fb_number - 1) * 14

    if start:
        guessed_date = base_date + datetime.timedelta(days=days_offset)
    else:
        guessed_date = base_date + datetime.timedelta(days=days_offset + 13)

    return guessed_date


def _get_fb_start_date(fb):
    if not fb.startswith('FB'):
        fb = 'FB' + fb

    if fb in _get_fb_dict():
        return _get_fb_dict()[fb].start_date
    else:
        print(f'Warning: FB {fb} not found in db cache')
        return _deduce_fb_date(fb, start=True)


def _get_fb_end_date(fb):
    if not fb.startswith('FB'):
        fb = 'FB' + fb

    if fb in _get_fb_dict():
        return _get_fb_dict()[fb].end_date
    else:
        print(f'Warning: FB {fb} not found in db cache')
        return _deduce_fb_date(fb, start=False)
