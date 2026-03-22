from unittest.mock import MagicMock

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from formguard.checks import BaseCheck
from formguard.forms import GuardedFormMixin
from formguard.widgets import HoneypotWidget


def _make_request():
    request = MagicMock()
    request.META = {'REMOTE_ADDR': '127.0.0.1'}
    return request


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
        assert 'fg_ia' in form.fields

    # mixin caches check instances on self._checks
    def test_caches_checks(self):
        form = SampleForm()
        assert hasattr(form, '_checks')
        assert len(form._checks) == 4

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

    # guard_fields renders all check fields as HTML
    def test_guard_fields_renders_all_check_fields(self):
        form = SampleForm()
        html = form.guard_fields
        assert 'name="website"' in html
        assert 'name="fg_token"' in html
        assert 'name="fg_nonce"' in html
        assert 'name="fg_js"' in html
        assert 'name="fg_ia"' in html
        assert 'name="name"' not in html
        assert 'name="email"' not in html

    # formguard_checks class attribute overrides global setting
    def test_per_form_checks(self):
        class HoneypotOnlyForm(GuardedFormMixin, forms.Form):
            formguard_checks = ['formguard.checks.FieldTrapCheck']
            name = forms.CharField()

        form = HoneypotOnlyForm()
        assert 'website' in form.fields
        assert 'fg_token' not in form.fields
        assert 'fg_nonce' not in form.fields

    # request kwarg is stored on the form
    def test_request_stored(self):
        request = _make_request()
        form = SampleForm(request=request)
        assert form.request is request

    # guard_failures initialized as empty list
    def test_guard_failures_initialized(self):
        form = SampleForm()
        assert form.guard_failures == []

    # request defaults to None when not passed
    def test_request_defaults_to_none(self):
        form = SampleForm()
        assert form.request is None


class IsValidTests(SimpleTestCase):
    # is_valid runs guard checks on valid form and returns True when all pass
    @override_settings(FORMGUARD_CHECKS=['formguard.checks.FieldTrapCheck'])
    def test_valid_form_passes_checks(self):
        from formguard.test import GuardedFormTestMixin

        mixin = GuardedFormTestMixin()
        data = {'name': 'Alice', 'email': 'alice@example.com', **mixin.guard_data()}
        form = SampleForm(data, request=_make_request())
        assert form.is_valid() is True
        assert form.guard_failures == []

    # is_valid skips guard checks when base validation fails
    @override_settings(FORMGUARD_CHECKS=['formguard.checks.FieldTrapCheck'])
    def test_invalid_form_skips_checks(self):
        data = {'website': 'http://spam.com'}  # missing required fields
        form = SampleForm(data, request=_make_request())
        assert form.is_valid() is False
        assert form.guard_failures == []  # checks never ran

    # guard failures populate form.errors and guard_failures
    @override_settings(FORMGUARD_CHECKS=['formguard.checks.FieldTrapCheck'])
    def test_guard_failure_populates_errors(self):
        data = {'name': 'Bot', 'email': 'bot@example.com', 'website': 'http://spam.com'}
        form = SampleForm(data, request=_make_request())
        assert form.is_valid() is False
        assert 'honeypot field filled' in form.guard_failures
        assert form.errors  # non-field errors present

    # is_valid raises ImproperlyConfigured when request is None
    @override_settings(FORMGUARD_CHECKS=['formguard.checks.FieldTrapCheck'])
    def test_missing_request_raises(self):
        data = {'name': 'Alice', 'email': 'alice@example.com', 'website': ''}
        form = SampleForm(data)  # no request
        with self.assertRaises(ImproperlyConfigured, msg='request=request'):
            form.is_valid()

    # is_valid called twice only runs checks once
    @override_settings(FORMGUARD_CHECKS=['formguard.checks.FieldTrapCheck'])
    def test_idempotent_is_valid(self):
        data = {'name': 'Bot', 'email': 'bot@example.com', 'website': 'http://spam.com'}
        form = SampleForm(data, request=_make_request())
        result1 = form.is_valid()
        result2 = form.is_valid()
        assert result1 == result2
        assert len(form.guard_failures) == 1  # only one entry, not two

    # multiple checks can fail and all are recorded
    def test_multiple_guard_failures(self):
        data = {
            'name': 'Bot',
            'email': 'bot@example.com',
            'website': 'http://spam.com',
            'fg_token': 'tampered',
            'fg_nonce': '',
            'fg_js': '',
            'fg_ia': '',
        }
        form = SampleForm(data, request=_make_request())
        assert form.is_valid() is False
        assert len(form.guard_failures) > 1

    # fail_open check that crashes is silently skipped
    @override_settings(
        FORMGUARD_CHECKS=['formguard.tests.test_checks.CrashingCheck']
    )
    def test_fail_open_crash_skipped(self):
        data = {'name': 'Alice', 'email': 'alice@example.com'}
        form = SampleForm(data, request=_make_request())
        assert form.is_valid() is True
        assert form.guard_failures == []

    # fail_closed check that crashes adds to guard_failures
    @override_settings(
        FORMGUARD_CHECKS=['formguard.tests.test_checks.CrashingFailClosedCheck']
    )
    def test_fail_closed_crash_recorded(self):
        data = {'name': 'Alice', 'email': 'alice@example.com'}
        form = SampleForm(data, request=_make_request())
        assert form.is_valid() is False
        assert 'check error' in form.guard_failures

    # signal fires when guard checks fail
    @override_settings(FORMGUARD_CHECKS=['formguard.checks.FieldTrapCheck'])
    def test_signal_fires_on_guard_failure(self):
        from formguard.signals import guard_triggered

        received = []

        def handler(sender, **kwargs):
            received.append(kwargs)

        guard_triggered.connect(handler)
        try:
            data = {'name': 'Bot', 'email': 'bot@example.com', 'website': 'http://spam.com'}
            form = SampleForm(data, request=_make_request())
            form.is_valid()
            assert len(received) == 1
            assert 'honeypot field filled' in received[0]['reasons']
        finally:
            guard_triggered.disconnect(handler)

    # signal does not fire when all checks pass
    @override_settings(FORMGUARD_CHECKS=['formguard.checks.FieldTrapCheck'])
    def test_signal_not_fired_on_clean_form(self):
        from formguard.signals import guard_triggered

        received = []

        def handler(sender, **kwargs):
            received.append(kwargs)

        guard_triggered.connect(handler)
        try:
            data = {'name': 'Alice', 'email': 'alice@example.com', 'website': ''}
            form = SampleForm(data, request=_make_request())
            form.is_valid()
            assert len(received) == 0
        finally:
            guard_triggered.disconnect(handler)


# Stub checks for collision testing
class DuplicateFieldCheckA(BaseCheck):
    def get_fields(self):
        return {'duplicate_field': forms.CharField()}

    def check(self, form):
        return False


class DuplicateFieldCheckB(BaseCheck):
    def get_fields(self):
        return {'duplicate_field': forms.CharField()}

    def check(self, form):
        return False
