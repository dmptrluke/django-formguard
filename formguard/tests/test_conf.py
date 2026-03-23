from django.test import SimpleTestCase, override_settings

from formguard.conf import DEFAULTS, default_checks, get_setting


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


class DefaultChecksTests(SimpleTestCase):
    # returns configured checks with no arguments
    def test_returns_configured(self):
        assert default_checks() == DEFAULTS['CHECKS']

    # returns a new list, not the original
    def test_returns_copy(self):
        result = default_checks()
        result.append('extra')
        assert 'extra' not in DEFAULTS['CHECKS']

    # respects FORMGUARD_CHECKS setting
    @override_settings(FORMGUARD_CHECKS=['formguard.checks.FieldTrapCheck'])
    def test_reads_from_settings(self):
        result = default_checks()
        assert result == ['formguard.checks.FieldTrapCheck']

    # include appends to configured checks
    def test_include(self):
        result = default_checks(include=['myapp.checks.Custom'])
        assert result == DEFAULTS['CHECKS'] + ['myapp.checks.Custom']

    # exclude removes from configured checks
    def test_exclude(self):
        result = default_checks(exclude=['formguard.checks.InteractionCheck'])
        assert 'formguard.checks.InteractionCheck' not in result
        assert len(result) == len(DEFAULTS['CHECKS']) - 1

    # include and exclude together
    def test_include_and_exclude(self):
        result = default_checks(
            include=['myapp.checks.Custom'],
            exclude=['formguard.checks.InteractionCheck'],
        )
        assert 'formguard.checks.InteractionCheck' not in result
        assert 'myapp.checks.Custom' in result

    # exclude works against custom settings
    @override_settings(
        FORMGUARD_CHECKS=[
            'formguard.checks.FieldTrapCheck',
            'formguard.checks.TokenCheck',
        ]
    )
    def test_exclude_with_custom_settings(self):
        result = default_checks(exclude=['formguard.checks.TokenCheck'])
        assert result == ['formguard.checks.FieldTrapCheck']
