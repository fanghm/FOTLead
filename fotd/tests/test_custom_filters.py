from django.test import TestCase
from django.utils.safestring import SafeString
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

class LinkifyPrTests(TestCase):
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

    def test_linkify_feature(self):
        input_text = "The FOTL is taking care of feature CB123456-CR, CB012842-SR and CNI-654321."
        expected_output = (
            'The FOTL is taking care of feature '
            '<a href="/backlog/CB123456-CR/" target="_blank">CB123456-CR</a>'
            ', <a href="/backlog/CB012842-SR/" target="_blank">CB012842-SR</a>'
            ' and <a href="/backlog/CNI-654321/" target="_blank">CNI-654321</a>.'
        )
        result = custom_filters.linkify(input_text)
        self.assertIsInstance(result, SafeString)
        self.assertEqual(result, expected_output)


    def test_linkify_normal_name(self):
        input_text = "Contact: Hao-William Hu (NSB)."
        expected_output = (
            'Contact: '
            '<a href="#" onclick="navigator.clipboard.writeText(\'Hao-William Hu (NSB)\'); alert(\'Copied: Hao-William Hu (NSB)\'); return false;">Hao-William Hu (NSB)</a>.'
        )
        result = custom_filters.linkify(input_text)
        self.assertIsInstance(result, SafeString)
        self.assertEqual(result, expected_output)

    def test_linkify_name_with_middle_name(self):
        input_text = "Contact: Marc Claramunt Codinas (Nokia)."
        expected_output = (
            'Contact: '
            '<a href="#" onclick="navigator.clipboard.writeText(\'Marc Claramunt Codinas (Nokia)\'); alert(\'Copied: Marc Claramunt Codinas (Nokia)\'); return false;">Marc Claramunt Codinas (Nokia)</a>.'
        )
        result = custom_filters.linkify(input_text)
        self.assertIsInstance(result, SafeString)
        self.assertEqual(result, expected_output)

    def test_linkify_name_with_number(self):
        input_text = "Contact: Lei 24. Wang (NSB)."
        expected_output = (
            'Contact: '
            '<a href="#" onclick="navigator.clipboard.writeText(\'Lei 24. Wang (NSB)\'); alert(\'Copied: Lei 24. Wang (NSB)\'); return false;">Lei 24. Wang (NSB)</a>.'
        )
        result = custom_filters.linkify(input_text)
        self.assertIsInstance(result, SafeString)
        self.assertEqual(result, expected_output)

    def test_linkify_no_match(self):
        input_text = "This string does not contain any PR numbers."
        expected_output = input_text
        result = custom_filters.linkify(input_text)
        self.assertIsInstance(result, SafeString)
        self.assertEqual(result, expected_output)