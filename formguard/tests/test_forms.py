from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from formguard.checks import BaseCheck
from formguard.forms import GuardedFormMixin
from formguard.widgets import HoneypotWidget


class SampleForm(GuardedFormMixin, forms.Form):
    name = forms.CharField()
    email = forms.EmailField()


class GuardedFormMixinTests(SimpleTestCase):
    # mixin aggregates fields from all configured checks
    def test_aggregates_check_fields(self):
        form = SampleForm()
        assert 'website' in form.fields
        assert 'fg_token' in form.fields
        assert 'fg_nonce' in form.fields
        assert 'fg_js' in form.fields

    # mixin caches check instances on self._checks
    def test_caches_checks(self):
        form = SampleForm()
        assert hasattr(form, '_checks')
        assert len(form._checks) == 3

    # honeypot field uses HoneypotWidget
    def test_honeypot_uses_widget(self):
        form = SampleForm()
        assert isinstance(form.fields['website'].widget, HoneypotWidget)

    # check field colliding with form field raises ImproperlyConfigured
    def test_check_field_collides_with_form_field(self):
        class BadForm(GuardedFormMixin, forms.Form):
            website = forms.CharField()

        with self.assertRaises(ImproperlyConfigured):
            BadForm()

    # two checks contributing same field name raises ImproperlyConfigured
    @override_settings(
        FORMGUARD_CHECKS=[
            'formguard.tests.test_forms.DuplicateFieldCheckA',
            'formguard.tests.test_forms.DuplicateFieldCheckB',
        ]
    )
    def test_inter_check_field_collision_raises(self):
        with self.assertRaises(ImproperlyConfigured):
            SampleForm()

    # media aggregates widget media and check get_media()
    def test_media_aggregation(self):
        form = SampleForm()
        media_str = str(form.media)
        assert 'formguard/formguard.css' in media_str
        assert 'formguard/formguard.js' in media_str

    # empty CHECKS setting produces form with no guard fields
    @override_settings(FORMGUARD_CHECKS=[])
    def test_empty_checks(self):
        form = SampleForm()
        assert 'website' not in form.fields
        assert 'fg_token' not in form.fields

    # formguard_checks class attribute overrides global setting
    def test_per_form_checks(self):
        class HoneypotOnlyForm(GuardedFormMixin, forms.Form):
            formguard_checks = ['formguard.checks.FieldTrapCheck']
            name = forms.CharField()

        form = HoneypotOnlyForm()
        assert 'website' in form.fields
        assert 'fg_token' not in form.fields
        assert 'fg_nonce' not in form.fields


# Stub checks for collision testing
class DuplicateFieldCheckA(BaseCheck):
    def get_fields(self):
        return {'duplicate_field': forms.CharField()}

    def check(self, request, form):
        return False


class DuplicateFieldCheckB(BaseCheck):
    def get_fields(self):
        return {'duplicate_field': forms.CharField()}

    def check(self, request, form):
        return False
