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


def _get_fbs(start_fb, end_fb):
    """
    Get a list of FBs between start_fb and end_fb, inclusive
    start_fb, end_fb in the string format without "FB" prefix, eg: '2325', '2401'
    """

    if not (start_fb and end_fb):
        return []
    elif start_fb >= end_fb:
        return [end_fb]
    else:
        fbs = [start_fb]
        start = int(start_fb)
        while start < int(end_fb):
            if start % 100 == 26:  # 26 fbs in each year
                start = (int(start / 100) + 1) * 100 + 1
            else:
                start += 1
            fbs.append(str(start))
        return fbs


def _get_fb_count(start_fb, end_fb):
    """
    Get the number of FBs between start_fb and end_fb, inclusive
    start_fb, end_fb in the string format without "FB" prefix, eg: '2325', '2401'
    NOTE: if start_fb is greater than end_fb, it will return 1
    """

    if not (start_fb and end_fb):
        return 0
    elif start_fb > end_fb:
        print(
            "WARNING: Start FB ({}) is greater than end FB ({})".format(
                start_fb, end_fb
            )
        )
        return 1
    elif start_fb == end_fb:
        return 1
    else:
        start_year = int(start_fb[:2])
        start_num = int(start_fb[2:])
        end_year = int(end_fb[:2])
        end_num = int(end_fb[2:])

        # Calculate the number of FBs in the start year
        fb_count_start_year = 26 - start_num + 1

        # Calculate the number of FBs in the end year
        fb_count_end_year = end_num

        # Calculate the number of FBs in the years between start and end
        fb_count_between_years = (end_year - start_year - 1) * 26

        # Total FB count
        total_fb_count = (
            fb_count_start_year + fb_count_between_years + fb_count_end_year
        )

        return total_fb_count


def _get_remaining_fb_count(start_fb, end_fb, current_fb):
    if start_fb is None or end_fb is None or current_fb is None:
        print(f"start_fb: {start_fb}, end_fb: {end_fb}, current_fb: {current_fb}")
        return 1

    remaining_fb_count = _get_fb_count(max(current_fb, start_fb), end_fb)
    return remaining_fb_count
