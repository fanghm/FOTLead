# test_globals.py
from django.test import TestCase
from django.core.cache import cache
from fotd.models import Sprint
from fotd.globals import _get_fb_start_date, _get_fb_end_date, CACHE_TIMEOUT
import datetime

class GlobalsTestCase(TestCase):
    def setUp(self):
        cache.clear()
        
        # prepare test data
        Sprint.objects.create(fb='FB2301', start_date=datetime.date(2023, 1, 4), end_date=datetime.date(2023, 1, 17))
        Sprint.objects.create(fb='FB2302', start_date=datetime.date(2023, 1, 18), end_date=datetime.date(2023, 1, 31))
        Sprint.objects.create(fb='FB2303', start_date=datetime.date(2023, 2, 1), end_date=datetime.date(2023, 2, 14))

    def test_get_fb_start_date(self):
        self.assertEqual(_get_fb_start_date('FB2301'), datetime.date(2023, 1, 4))
        self.assertEqual(_get_fb_start_date('FB2302'), datetime.date(2023, 1, 18))
        self.assertEqual(_get_fb_start_date('FB2303'), datetime.date(2023, 2, 1))

        # test getting start date for non-existent FB
        self.assertIsNone(_get_fb_start_date('FB9999'))

    def test_get_fb_end_date(self):
        self.assertEqual(_get_fb_end_date('FB2301'), datetime.date(2023, 1, 17))
        self.assertEqual(_get_fb_end_date('FB2302'), datetime.date(2023, 1, 31))
        self.assertEqual(_get_fb_end_date('FB2303'), datetime.date(2023, 2, 14))

        # test getting end date for non-existent FB
        self.assertIsNone(_get_fb_end_date('FB9999'))

    def test_cache(self):
        _get_fb_start_date('FB2301')  # trigger cache set
        self.assertIsNotNone(cache.get('fb_dict'))

        # test cache timeout
        cache.set('fb_dict', {'FB2301': (datetime.date(2023, 1, 4), datetime.date(2023, 1, 17))}, timeout=1)
        self.assertIsNotNone(cache.get('fb_dict'))
        import time
        time.sleep(2)
        self.assertIsNone(cache.get('fb_dict'))