import time
from unittest.mock import MagicMock, patch

from django.core import signing
from django.test import SimpleTestCase, override_settings

from formguard.checks import field_trap, js_challenge, run_checks, signature, timing


def _js_response(token_value):
    """Compute the expected JS challenge response for a token."""
    return format(sum(ord(c) for c in token_value) & 0xFFFF, 'x')


def _make_form(field_name='website', field_value='', token_name='fg_token', token_value=None):
    """Build a mock form with cleaned_data for testing checks."""
    if token_value is None:
        token_value = signing.dumps(time.time() - 10, salt='formguard')
    form = MagicMock()
    form.cleaned_data = {
        field_name: field_value,
        token_name: token_value,
        'fg_js': _js_response(token_value),
    }
    return form


def _make_request(remote_addr='127.0.0.1'):
    request = MagicMock()
    request.META = {'REMOTE_ADDR': remote_addr}
    return request


class FieldTrapTests(SimpleTestCase):
    # empty field passes
    def test_empty_field_passes(self):
        form = _make_form(field_value='')
        assert field_trap(_make_request(), form) is False

    # filled field triggers
    def test_filled_field_triggers(self):
        form = _make_form(field_value='http://spam.com')
        result = field_trap(_make_request(), form)
        assert isinstance(result, str)

    # whitespace-only field triggers (any non-empty = bot)
    def test_whitespace_triggers(self):
        form = _make_form(field_value=' ')
        result = field_trap(_make_request(), form)
        assert isinstance(result, str)

    # respects custom field name setting
    @override_settings(FORMGUARD_FIELD_NAME='phone')
    def test_custom_field_name(self):
        form = _make_form(field_name='phone', field_value='555-1234')
        result = field_trap(_make_request(), form)
        assert isinstance(result, str)


class TimingTests(SimpleTestCase):
    # submission after min_seconds passes
    def test_slow_submission_passes(self):
        token = signing.dumps(time.time() - 10, salt='formguard')
        form = _make_form(token_value=token)
        assert timing(_make_request(), form) is False

    # submission before min_seconds triggers
    def test_fast_submission_triggers(self):
        token = signing.dumps(time.time(), salt='formguard')
        form = _make_form(token_value=token)
        result = timing(_make_request(), form)
        assert isinstance(result, str)

    # respects custom min_seconds setting
    @override_settings(FORMGUARD_MIN_SECONDS=10)
    def test_custom_min_seconds(self):
        token = signing.dumps(time.time() - 5, salt='formguard')
        form = _make_form(token_value=token)
        result = timing(_make_request(), form)
        assert isinstance(result, str)


class SignatureTests(SimpleTestCase):
    # valid signature passes
    def test_valid_signature_passes(self):
        token = signing.dumps(time.time() - 10, salt='formguard')
        form = _make_form(token_value=token)
        assert signature(_make_request(), form) is False

    # tampered signature triggers
    def test_tampered_signature_triggers(self):
        form = _make_form(token_value='tampered-garbage')
        result = signature(_make_request(), form)
        assert isinstance(result, str)

    # missing token triggers
    def test_missing_token_triggers(self):
        form = _make_form(token_value='')
        result = signature(_make_request(), form)
        assert isinstance(result, str)

    # expired token triggers (sign at a time >max_age seconds ago)
    def test_expired_token_triggers(self):
        old_time = time.time() - 7200
        with patch('django.core.signing.time.time', return_value=old_time):
            token = signing.dumps(old_time, salt='formguard')
        form = _make_form(token_value=token)
        result = signature(_make_request(), form)
        assert isinstance(result, str)


class RunChecksTests(SimpleTestCase):
    # all checks pass returns empty list
    def test_all_pass(self):
        form = _make_form()
        reasons = run_checks(_make_request(), form)
        assert reasons == []

    # triggered checks are collected in reasons list
    def test_triggered_check_returns_reasons(self):
        form = _make_form(field_value='spam')
        reasons = run_checks(_make_request(), form)
        assert len(reasons) >= 1

    # crashing check is logged and skipped (fail-open)
    @override_settings(FORMGUARD_CHECKS=['formguard.tests.test_checks.bad_check'])
    def test_crashing_check_skipped(self):
        form = _make_form()
        reasons = run_checks(_make_request(), form)
        assert reasons == []

    # custom check in pipeline is called
    @override_settings(FORMGUARD_CHECKS=['formguard.tests.test_checks.always_triggers'])
    def test_custom_check(self):
        form = _make_form()
        reasons = run_checks(_make_request(), form)
        assert 'always' in reasons[0]


class JsChallengeTests(SimpleTestCase):
    # JS field with correct computed value passes
    def test_correct_js_value_passes(self):
        token = signing.dumps(time.time() - 10, salt='formguard')
        form = MagicMock()
        form.cleaned_data = {
            'website': '',
            'fg_token': token,
            'fg_js': _js_response(token),
        }
        assert js_challenge(_make_request(), form) is False

    # empty JS field triggers
    def test_empty_js_field_triggers(self):
        token = signing.dumps(time.time() - 10, salt='formguard')
        form = MagicMock()
        form.cleaned_data = {
            'website': '',
            'fg_token': token,
            'fg_js': '',
        }
        result = js_challenge(_make_request(), form)
        assert isinstance(result, str)

    # wrong JS field value triggers
    def test_wrong_js_value_triggers(self):
        token = signing.dumps(time.time() - 10, salt='formguard')
        form = MagicMock()
        form.cleaned_data = {
            'website': '',
            'fg_token': token,
            'fg_js': 'wrongval',
        }
        result = js_challenge(_make_request(), form)
        assert isinstance(result, str)

    # missing JS field triggers
    def test_missing_js_field_triggers(self):
        token = signing.dumps(time.time() - 10, salt='formguard')
        form = MagicMock()
        form.cleaned_data = {
            'website': '',
            'fg_token': token,
        }
        result = js_challenge(_make_request(), form)
        assert isinstance(result, str)


def bad_check(request, form):
    raise RuntimeError('boom')


def always_triggers(request, form):
    return 'always triggers'
