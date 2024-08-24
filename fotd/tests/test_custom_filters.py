from django.test import TestCase
from django.utils.safestring import SafeString, mark_safe
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

    def test_linkify_normal_name(self):
        input_text = "Waiting feedback from Wei-William Lee (NSB)."
        expected_output = (
            'Waiting feedback from '
            '<a href="#copy-to-clipboard" onclick="navigator.clipboard.writeText(\'Wei-William Lee (NSB)\'); alert(\'Name copied: Wei-William Lee (NSB)\'); return false;">Wei-William Lee (NSB)</a>.'
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

    def test_linkify_name_with_middle_name(self):
        input_text = "Contact: Mask M. Mike (Nokia)."
        expected_output = (
            'Contact: '
            '<a href="#copy-to-clipboard" onclick="navigator.clipboard.writeText(\'Mask M. Mike (Nokia)\'); alert(\'Name copied: Mask M. Mike (Nokia)\'); return false;">Mask M. Mike (Nokia)</a>.'
        )
        result = custom_filters.linkify(input_text)
        self.assertIsInstance(result, SafeString)
        self.assertEqual(result, expected_output)

    def test_linkify_name_with_number(self):
        input_text = "Contact: Hua 77. Zhao (NSB)."
        expected_output = (
            'Contact: '
            '<a href="#copy-to-clipboard" onclick="navigator.clipboard.writeText(\'Hua 77. Zhao (NSB)\'); alert(\'Name copied: Hua 77. Zhao (NSB)\'); return false;">Hua 77. Zhao (NSB)</a>.'
        )
        result = custom_filters.linkify(input_text)
        self.assertIsInstance(result, SafeString)
        self.assertEqual(result, expected_output)

    def test_linkify_short_url(self):
        self.assertEqual(
            custom_filters.linkify('This is a short URL: https://example.com/short.'),
            mark_safe('This is a short URL: <a href="https://example.com/short" target="_blank">https://example.com/short</a>.')
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