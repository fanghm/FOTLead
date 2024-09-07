# globals.py
from django.core.cache import cache
from collections import namedtuple
from django.db.models import QuerySet
from .models import Sprint

CACHE_TIMEOUT = 3600 * 24  # 24 hours
SprintDates = namedtuple('SprintDates', ['start_date', 'end_date'])

def _query_database_for_fb_dict():
    print("Querying database for FB data")
    sprints = Sprint.objects.values('fb', 'start_date', 'end_date')
    fb_dict = {sprint['fb']: SprintDates(sprint['start_date'], sprint['end_date']) for sprint in sprints}
    
    print(f'FB dict size: {len(fb_dict)}')
    return fb_dict

def _get_fb_dict():
    fb_dict = cache.get('fb_dict')
    if fb_dict is None:
        fb_dict = _query_database_for_fb_dict()
        cache.set('fb_dict', fb_dict, timeout=CACHE_TIMEOUT)

    return fb_dict

def _get_fb_start_date(fb):
    if not fb.startswith('FB'):
        fb = 'FB' + fb
    return _get_fb_dict()[fb].start_date if fb in _get_fb_dict() else None
    

def _get_fb_end_date(fb):
    if not fb.startswith('FB'):
        fb = 'FB' + fb
    return _get_fb_dict()[fb].end_date if fb in _get_fb_dict() else None
