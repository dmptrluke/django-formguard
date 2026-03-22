from django.test import SimpleTestCase

from formguard.conf import get_setting


class GetSettingTests(SimpleTestCase):
    # returns default check list
    def test_default_checks(self):
        checks = get_setting('CHECKS')
        assert checks == [
            'formguard.checks.FieldTrapCheck',
            'formguard.checks.TokenCheck',
            'formguard.checks.JsChallengeCheck',
            'formguard.checks.InteractionCheck',
        ]
