from unittest.mock import MagicMock

from django import forms
from django.test import SimpleTestCase, override_settings

from formguard.checks import resolve_checks, run_checks
from formguard.conf import get_config
from formguard.forms import GuardedFormMixin
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
        form._checks = resolve_checks(get_config('CHECKS'))
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

    # form_class with guard_checks=None uses global checks
    def test_form_class_with_global_checks(self):
        class GlobalChecksForm(GuardedFormMixin, forms.Form):
            name = forms.CharField()

        data = self.guard_data(form_class=GlobalChecksForm)
        assert 'website' in data
        assert 'fg_token' in data

    # form_class with explicit guard_checks uses those checks
    def test_form_class_with_explicit_checks(self):
        class ExplicitChecksForm(GuardedFormMixin, forms.Form):
            guard_checks = ['formguard.checks.FieldTrapCheck']
            name = forms.CharField()

        data = self.guard_data(form_class=ExplicitChecksForm)
        assert 'website' in data
        assert 'fg_token' not in data

    # form_class with guard_check_options passes options through
    @override_settings(FORMGUARD_CHECKS=['formguard.checks.FieldTrapCheck'])
    def test_form_class_with_check_options(self):
        class OptionsForm(GuardedFormMixin, forms.Form):
            guard_check_options = {
                'formguard.checks.FieldTrapCheck': {'FIELD_NAME': 'phone'},
            }
            name = forms.CharField()

        data = self.guard_data(form_class=OptionsForm)
        assert 'phone' in data
        assert 'website' not in data
