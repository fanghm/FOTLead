from django.test import TestCase
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