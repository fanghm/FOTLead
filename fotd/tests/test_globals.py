# test_globals.py
import datetime
import time

from django.core.cache import cache
from django.test import TestCase

from fotd.globals import (
    _deduce_fb_date,
    _get_fb_end_date,
    _get_fb_start_date,
    _get_remaining_fb_count,
)
from fotd.models import Sprint


class GlobalsTestCase(TestCase):
    def setUp(self):
        cache.clear()

        # prepare test data
        Sprint.objects.create(
            fb='FB2301',
            start_date=datetime.date(2023, 1, 4),
            end_date=datetime.date(2023, 1, 17),
        )
        Sprint.objects.create(
            fb='FB2302',
            start_date=datetime.date(2023, 1, 18),
            end_date=datetime.date(2023, 1, 31),
        )
        Sprint.objects.create(
            fb='FB2303',
            start_date=datetime.date(2023, 2, 1),
            end_date=datetime.date(2023, 2, 14),
        )

    def test_deduce_start_date(self):
        self.assertEqual(_deduce_fb_date('FB2501', True), datetime.date(2025, 1, 1))
        self.assertEqual(_deduce_fb_date('FB2502', True), datetime.date(2025, 1, 15))
        self.assertEqual(_deduce_fb_date('FB2503', True), datetime.date(2025, 1, 29))
        self.assertEqual(_deduce_fb_date('FB2504', True), datetime.date(2025, 2, 12))

    def test_deduce_end_date(self):
        self.assertEqual(_deduce_fb_date('FB2501', False), datetime.date(2025, 1, 14))
        self.assertEqual(_deduce_fb_date('FB2502', False), datetime.date(2025, 1, 28))
        self.assertEqual(_deduce_fb_date('FB2503', False), datetime.date(2025, 2, 11))
        self.assertEqual(_deduce_fb_date('FB2504', False), datetime.date(2025, 2, 25))

    def test_get_fb_start_date(self):
        self.assertEqual(_get_fb_start_date('FB2301'), datetime.date(2023, 1, 4))
        self.assertEqual(_get_fb_start_date('FB2302'), datetime.date(2023, 1, 18))
        self.assertEqual(_get_fb_start_date('FB2303'), datetime.date(2023, 2, 1))

        # test getting start date for not defined FB
        self.assertIsNotNone(_get_fb_start_date('FB2801'))

    def test_get_fb_end_date(self):
        self.assertEqual(_get_fb_end_date('FB2301'), datetime.date(2023, 1, 17))
        self.assertEqual(_get_fb_end_date('FB2302'), datetime.date(2023, 1, 31))
        self.assertEqual(_get_fb_end_date('FB2303'), datetime.date(2023, 2, 14))

        # test getting end date for not defined FB
        self.assertIsNotNone(_get_fb_end_date('FB2926'))

    def test_cache(self):
        _get_fb_start_date('FB2301')  # trigger cache set
        self.assertIsNotNone(cache.get('fb_dict'))

        # test cache timeout
        cache.set(
            'fb_dict',
            {'FB2301': (datetime.date(2023, 1, 4), datetime.date(2023, 1, 17))},
            timeout=1,
        )

        self.assertIsNotNone(cache.get('fb_dict'))
        time.sleep(2)
        self.assertIsNone(cache.get('fb_dict'))

    def test_get_remaining_fb_count(self):
        # Test cases for _get_remaining_fb_count
        self.assertEqual(_get_remaining_fb_count('2301', '2305', '2302'), 4)
        self.assertEqual(_get_remaining_fb_count('2301', '2305', '2305'), 1)
        self.assertEqual(_get_remaining_fb_count('2301', '2305', '2306'), 1)
        self.assertEqual(_get_remaining_fb_count('2301', '2305', '2225'), 5)
        self.assertEqual(_get_remaining_fb_count('2301', '2301', '2301'), 1)
        self.assertEqual(_get_remaining_fb_count('2301', '2301', '2225'), 1)
