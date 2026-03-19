from django.test import SimpleTestCase, override_settings

from formguard.conf import get_setting


class GetSettingTests(SimpleTestCase):
    # returns default when setting is not configured
    def test_default_field_name(self):
        assert get_setting('FIELD_NAME') == 'website'

    def test_default_min_seconds(self):
        assert get_setting('MIN_SECONDS') == 3

    def test_default_max_seconds(self):
        assert get_setting('MAX_SECONDS') == 3600

    def test_default_success_message(self):
        assert get_setting('SUCCESS_MESSAGE') is None

    def test_default_checks(self):
        checks = get_setting('CHECKS')
        assert checks == [
            'formguard.checks.field_trap',
            'formguard.checks.timing',
            'formguard.checks.signature',
            'formguard.checks.js_challenge',
        ]

    # user override is respected
    @override_settings(FORMGUARD_FIELD_NAME='phone')
    def test_override_setting(self):
        assert get_setting('FIELD_NAME') == 'phone'
