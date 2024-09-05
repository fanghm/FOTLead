from datetime import datetime, timedelta
from django.test import TestCase
from django.utils.safestring import SafeString, mark_safe
from django.utils.timesince import timesince
from fotd.templatetags import custom_filters

class CustomFiltersTest(TestCase):
	def test_replace(self):
		self.assertEqual(custom_filters.replace('hello world', 'world,universe'), 'hello universe')

	def test_startswith(self):
		self.assertTrue(custom_filters.startswith('hello world', 'hello'))
		self.assertFalse(custom_filters.startswith('hello world', 'world'))

	def test_keyvalue(self):
		self.assertEqual(custom_filters.keyvalue({'key': 'value'}, 'key'), 'value')
		self.assertEqual(custom_filters.keyvalue({'key': 'value'}, 'nonexistent'), '')

	def test_get_previous_end_fb(self):
		endfb_changed_items = {'item1': {'previous': 'value1'}}
		self.assertEqual(custom_filters.get_previous_end_fb(endfb_changed_items, 'item1'), 'value1')
		self.assertEqual(custom_filters.get_previous_end_fb(endfb_changed_items, 'item2'), 'blank')

class RoughTimeSinceTests(TestCase):
    def _normalize_time_string(self, time_string):
        return time_string.replace('\xa0', ' ') # replace non-breaking space '\xa0' with regular space

    def test_roughtime_since_days(self):
        now = datetime.now()
        three_days_ago = now - timedelta(days=3)
        result = self._normalize_time_string(custom_filters.roughtime_since(three_days_ago))
        self.assertEqual(result, '3 days')

    def test_roughtime_since_weeks(self):
        now = datetime.now()
        two_weeks_ago = now - timedelta(weeks=2)
        result = self._normalize_time_string(custom_filters.roughtime_since(two_weeks_ago))
        self.assertEqual(result, '2 weeks')

    def test_roughtime_since_months(self):
        now = datetime.now()
        two_months_ago = now - timedelta(days=70)   # 60 days -> 1 month, 4 weeks
        result = self._normalize_time_string(custom_filters.roughtime_since(two_months_ago))
        self.assertTrue('2 months' in result)

    def test_roughtime_since_years(self):
        now = datetime.now()
        one_year_ago = now - timedelta(days=385)    # 365 days -> 11 months, 4 weeks
        result = self._normalize_time_string(custom_filters.roughtime_since(one_year_ago))
        self.assertTrue('1 year' in result)

    def test_roughtime_since_invalid_type(self):
        self.assertEqual(custom_filters.roughtime_since("not a datetime"), "not a datetime")

class LinkifyTests(TestCase):
    def test_linkify_pr(self):
        input_text = "Here is a PR number: PR123456, and one more: PR654321."
        expected_output = (
            'Here is a PR number: '
            '<a href="https://pronto.ext.net.nokia.com/pronto/problemReportSearch.html?freeTextdropDownID=prId&searchTopText=PR123456" target="_blank">PR123456</a>'
            ', and one more: '
            '<a href="https://pronto.ext.net.nokia.com/pronto/problemReportSearch.html?freeTextdropDownID=prId&searchTopText=PR654321" target="_blank">PR654321</a>.'
        )
        result = custom_filters.linkify(input_text)
        self.assertIsInstance(result, SafeString)
        self.assertEqual(result, expected_output)

    def test_linkify_feature_id(self):
        input_text = "The FOTL is taking care of feature CB8701, CB123456, CB012842-CR and CNI-654321."
        expected_output = (
            'The FOTL is taking care of feature '
            '<a href="/backlog/CB008701-SR/" target="_blank">CB8701</a>'
            ', <a href="/backlog/CB123456-SR/" target="_blank">CB123456</a>'
            ', <a href="/backlog/CB012842-CR/" target="_blank">CB012842-CR</a>'
            ' and <a href="/backlog/CNI-654321/" target="_blank">CNI-654321</a>.'
        )
        result = custom_filters.linkify(input_text)
        self.assertIsInstance(result, SafeString)
        self.assertEqual(result, expected_output)

    def test_linkify_names(self):
        test_names = {
            "regular_name": "Wei-William Lee (NSB)",
            "name_with_number": "Hua 77. Zhao (NSB)",
            "name_with_middle_name": "Mask M. Mike (Nokia)",
        }
    
        for name_type, name in test_names.items():
            with self.subTest(test_name=f'test_linkify_{name_type}'):
                input_text = f"Contact: {name}."
                expected_output = (
                    'Contact: '
                    f'<a href="#copy-to-clipboard" onclick="navigator.clipboard.writeText(\'{name}\'); alert(\'Name copied: {name}\'); return false;">{name}</a>.'
                )
                result = custom_filters.linkify(input_text)
                self.assertIsInstance(result, SafeString)
                self.assertEqual(result, expected_output)

    def test_linkify_normal_name_and_feature_id(self):
        input_text = "Waiting feedback from CB9999 FOTL Frankson Smith (Nokia)"
        expected_output = (
            'Waiting feedback from '
            '<a href="/backlog/CB009999-SR/" target="_blank">CB9999</a> FOTL <a href="#copy-to-clipboard" onclick="navigator.clipboard.writeText(\'Frankson Smith (Nokia)\'); alert(\'Name copied: Frankson Smith (Nokia)\'); return false;">Frankson Smith (Nokia)</a>'
        )
        result = custom_filters.linkify(input_text)
        self.assertIsInstance(result, SafeString)
        self.assertEqual(result, expected_output)

    def test_linkify_short_url(self):
        self.assertEqual(
            custom_filters.linkify('This is a short URL: https://example.com/short.'),
            mark_safe('This is a short URL: <a href="https://example.com/short" target="_blank">https://example.com/short</a>.')
        )

    def test_linkify_short_url2(self):
        self.assertEqual(
            custom_filters.linkify('Combined PGO knife is ready at: https://es-si-s3-z2.eecloud.nsn-net.net/knife-results/1231165/s3_packages_list.html'),
            mark_safe('Combined PGO knife is ready at: <a href="https://es-si-s3-z2.eecloud.nsn-net.net/knife-results/1231165/s3_packages_list.html" target="_blank">https://es-si-s3-z2....3_packages_list.html</a>')
        )

    def test_linkify_short_url_with_feature_id(self):
        self.assertEqual(
            custom_filters.linkify('This is a short URL: http://example.com/short/feature/CB11098/.'),
            mark_safe('This is a short URL: <a href="http://example.com/short/feature/CB11098/" target="_blank">http://example.com/short/feature/CB11098/</a>.')
        )

    def test_linkify_short_url_with_pr_id(self):
        self.assertEqual(
            custom_filters.linkify('This is a short URL: https://example.com/PR911911.'),
            mark_safe('This is a short URL: <a href="https://example.com/PR911911" target="_blank">https://example.com/PR911911</a>.')
        )

    def test_linkify_long_url_and_truncate(self):
        self.assertEqual(
            custom_filters.linkify('This is a long URL: https://example.com/some/really/long/url/that/needs/to/be/truncated/because/it/is/too/long.'),
            mark_safe('This is a long URL: <a href="https://example.com/some/really/long/url/that/needs/to/be/truncated/because/it/is/too/long" target="_blank">https://example.com/...cause/it/is/too/long</a>.')
        )

    def test_linkify_with_long_url_and_feature_id(self):
        self.assertEqual(
            custom_filters.linkify('This is a long URL: https://example.com/some/really/long/url/with/feature/id/but/should/not/add/extra/link/CB011098.'),
            mark_safe('This is a long URL: <a href="https://example.com/some/really/long/url/with/feature/id/but/should/not/add/extra/link/CB011098" target="_blank">https://example.com/.../extra/link/CB011098</a>.')
        )

    def test_linkify_with_long_url_and_feature_pr_id(self):
        self.assertEqual(
            custom_filters.linkify('This is a long URL: https://example.com/some/really/long/url/with/feature/and/pr/id/but/should/not/add/extra/link/PR123456/and/CB011098.'),
            mark_safe('This is a long URL: <a href="https://example.com/some/really/long/url/with/feature/and/pr/id/but/should/not/add/extra/link/PR123456/and/CB011098" target="_blank">https://example.com/...R123456/and/CB011098</a>.')
        )

    def test_linkify_no_match(self):
        input_text = "This string does not contain any PR numbers."
        expected_output = input_text
        result = custom_filters.linkify(input_text)
        self.assertIsInstance(result, SafeString)
        self.assertEqual(result, expected_output)