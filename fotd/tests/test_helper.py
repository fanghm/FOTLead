from django.test import TestCase
from fotd.helper import calc_release_per_priority, get_feature_boundary_category

class TestCalcReleasePerPriority(TestCase):
    def test_calc_release_per_priority(self):
        # tests of supported priority
        self.assertEqual(calc_release_per_priority(32000), '24R2')
        self.assertEqual(calc_release_per_priority(32999), '24R2')

        self.assertEqual(calc_release_per_priority(34000), '24R3')
        self.assertEqual(calc_release_per_priority(34999), '24R3')

        self.assertEqual(calc_release_per_priority(36000), '25R1')
        self.assertEqual(calc_release_per_priority(36999), '25R1')

        self.assertEqual(calc_release_per_priority(38000), '25R2')
        self.assertEqual(calc_release_per_priority(38999), '25R2')

        self.assertEqual(calc_release_per_priority(40000), '25R3')
        self.assertEqual(calc_release_per_priority(40999), '25R3')

        # tests of futher release priority
        self.assertEqual(calc_release_per_priority(42000), '26R1')
        self.assertEqual(calc_release_per_priority(42999), '26R1')
        
        # tests of not supported or incorrect priority
        self.assertEqual(calc_release_per_priority(30000), None)
        self.assertEqual(calc_release_per_priority(33000), None)
        self.assertEqual(calc_release_per_priority(41000), None)

class TestFeatureBoundaryCategory(TestCase):
    def test_get_feature_boundary_category(self):
        # 测试不同的优先级和 csr_list 对应的边界类型
        self.assertEqual(get_feature_boundary_category(34000, ['24R3']), [('24R3', 'Regular')])
        self.assertEqual(get_feature_boundary_category(34000, ['24R3', '25R1']), [('24R3', 'Outgoing LLF'), ('25R1', 'LLF incoming')])
        self.assertEqual(get_feature_boundary_category(34000, ['24R3', '25R1', '25R2']), [('24R3', 'Outgoing eLLF'), ('25R2', 'eLLF incoming')])

        self.assertEqual(get_feature_boundary_category(36000, ['25R1']), [('25R1', 'Regular')])
        self.assertEqual(get_feature_boundary_category(36000, ['25R1', '25R2']), [('25R1', 'Outgoing LLF'), ('25R2', 'LLF incoming')])
        self.assertEqual(get_feature_boundary_category(36000, ['25R1', '25R2', '25R3']), [('25R1', 'Outgoing eLLF'), ('25R3', 'eLLF incoming')])

        self.assertEqual(get_feature_boundary_category(38000, ['25R2']), [('25R2', 'Regular')])
        self.assertEqual(get_feature_boundary_category(38000, ['25R2', '25R3']), [('25R2', 'Outgoing LLF'), ('25R3', 'LLF incoming')])
        self.assertEqual(get_feature_boundary_category(38000, ['25R2', '25R3', '26R1']), [('25R2', 'Outgoing eLLF'), ('26R1', 'eLLF incoming')])

        self.assertEqual(get_feature_boundary_category(40000, ['25R3']), [('25R3', 'Regular')])
        self.assertEqual(get_feature_boundary_category(40000, ['25R3', '26R1']), [('25R3', 'Outgoing LLF'), ('26R1', 'LLF incoming')])
        self.assertEqual(get_feature_boundary_category(40000, ['25R3', '26R1', '26R2']), [('25R3', 'Outgoing eLLF'), ('26R2', 'eLLF incoming')])
        # 测试无效的优先级和 csr_list
        self.assertEqual(get_feature_boundary_category(31000, ['24R1']), None)
        self.assertEqual(get_feature_boundary_category(34000, []), None)
        self.assertEqual(get_feature_boundary_category(34000, ['24R2']), None)
