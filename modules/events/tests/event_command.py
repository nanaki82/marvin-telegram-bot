import unittest

from unittest_data_provider import data_provider
from modules.events.event_command import EventCommand


class TestEventCommand(unittest.TestCase):
    def setUp(self):
        self.evt_cmd = EventCommand({'events': {'create': 'anyone', 'publish': 'owner'}})

    allowed_users = lambda : (
        ((999, 'nickname'),),
        ((123, 'bla'),)
    )

    not_allowed_user = lambda : (
        ((999, 'turuttutu'),),
        ((666, 'bla'),)
    )

    @data_provider(allowed_users)
    def test_check_permission_ALLOW_with_username_or_userid(self, user):
        evt_cmd = EventCommand({'create': ['nickname', 123], 'publish': 'owner'})
        result = evt_cmd.check_permission('create', user)

        self.assertTrue(result)

    @data_provider(not_allowed_user)
    def test_check_permission_FAIL_with_username_or_userid(self, user):
        evt_cmd = EventCommand({'create': ['nickname', 123], 'publish': 'owner'})
        result = evt_cmd.check_permission('create', user)

        self.assertFalse(result)

    def test_check_permission_ALLOW_anyone(self):
        evt_cmd = EventCommand({'create': ['anyone', 123], 'publish': 'owner'})
        result = evt_cmd.check_permission('create', (123456789, 'qwertyuio'))

        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
