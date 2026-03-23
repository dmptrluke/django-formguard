from unittest.mock import MagicMock

from django.test import SimpleTestCase, override_settings

from formguard.checks import get_checks, run_checks
from formguard.test import GuardedFormTestMixin


class GuardedFormTestMixinTests(GuardedFormTestMixin, SimpleTestCase):
    # guard_data aggregates test_data from all active checks
    def test_guard_data_has_all_check_fields(self):
        data = self.guard_data()
        assert 'website' in data
        assert 'fg_token' in data
        assert 'fg_nonce' in data
        assert 'fg_js' in data

    # guard_data produces valid data (all checks pass)
    def test_guard_data_passes_all_checks(self):
        data = self.guard_data()
        form = MagicMock()
        form.cleaned_data = data
        form._checks = get_checks()
        results = run_checks(form)
        assert all(r.passed for r in results)

    # overrides are applied on top of generated data
    def test_overrides_applied(self):
        data = self.guard_data(website='http://spam.com')
        assert data['website'] == 'http://spam.com'

    # adapts to custom check configuration
    @override_settings(FORMGUARD_CHECKS=['formguard.checks.FieldTrapCheck'])
    def test_adapts_to_check_config(self):
        data = self.guard_data()
        assert 'website' in data
        assert 'fg_token' not in data
        assert 'fg_nonce' not in data
