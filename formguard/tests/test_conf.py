from django.test import SimpleTestCase, override_settings

from formguard.conf import get_setting


class GetSettingTests(SimpleTestCase):
    # returns default when setting is not configured
    def test_default_success_message(self):
        assert get_setting('SUCCESS_MESSAGE') is None

    def test_default_checks(self):
        checks = get_setting('CHECKS')
        assert checks == [
            'formguard.checks.FieldTrapCheck',
            'formguard.checks.TokenCheck',
            'formguard.checks.JsChallengeCheck',
        ]

    # user override is respected
    @override_settings(FORMGUARD_SUCCESS_MESSAGE='Thank you!')
    def test_override_setting(self):
        assert get_setting('SUCCESS_MESSAGE') == 'Thank you!'
