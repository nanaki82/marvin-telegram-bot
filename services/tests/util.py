import unittest

from unittest_data_provider import data_provider
from unittest.mock import MagicMock

from exceptions import *
from services.util import Util


class TestUtilModule(unittest.TestCase):
    def setUp(self):
        self.util = Util()

    correct_dictionaries = lambda : (
            ({}, {}),
            ({'telegram': 'fake_value'},
             {'telegram': '123456789qwertyuiopasdfghjk', 'env': 'production'}),
            ({'telegram': {'token': 'fake_value'}},
             {'telegram': {'token': {'123456789qwertyuiopasdfghjk'}, 'other': 42}, 'env': 'production'}))

    wrong_dictionaries = lambda : (
            ({'first': 'fake_value'},
             {},
             'first'),
            ({'second': 'fake_value'},
             {'second': None},
             'second'),
            ({'third': {'token': 'fake_value'}},
             {'third': {'token': None}},
             'token'),
            ({'fourth': {'token': {'nested': 'fake_value'}}},
             {'fourth': {'token': {'other': 'bla'}}},
             'nested'),
        )

    @data_provider(correct_dictionaries)
    def test_is_sub_dictionary(self, sub_dictionary, dictionary):
        (ok, failing_key) = self.util.is_sub_dict(sub_dictionary, dictionary)

        self.assertTrue(ok)

    @data_provider(wrong_dictionaries)
    def test_is_NOT_sub_dictionary(self, sub_dictionary, dictionary, failing_key_expected):
        (ok, failing_key) = self.util.is_sub_dict(sub_dictionary, dictionary)

        self.assertFalse(ok)
        self.assertEqual(failing_key, failing_key_expected)

    def test_check_config_exception(self):
        self.util.is_sub_dict = MagicMock(return_value=(False, 'pippo'))

        self.assertRaises(MissingConfigParameterError, self.util.check_config, config={'telegram': {'token': 'fake'}})


if __name__ == '__main__':
    unittest.main()
