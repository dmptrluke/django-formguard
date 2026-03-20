import time
from unittest.mock import MagicMock, patch

from django.core import signing
from django.core.exceptions import ImproperlyConfigured
from django.forms import CharField, HiddenInput, Media
from django.test import SimpleTestCase, override_settings

import pytest

from formguard.checks import (
    SIGNING_SALT,
    BaseCheck,
    FieldTrapCheck,
    JsChallengeCheck,
    TokenCheck,
    get_checks,
    run_checks,
)
from formguard.widgets import HoneypotWidget

# -- Stub checks for testing --


class PassingCheck(BaseCheck):
    def check(self, request, form):
        return False


class FailingCheck(BaseCheck):
    def check(self, request, form):
        return 'check failed'


class CrashingCheck(BaseCheck):
    fail_open = True

    def check(self, request, form):
        raise RuntimeError('boom')


class CrashingFailClosedCheck(BaseCheck):
    fail_open = False

    def check(self, request, form):
        raise RuntimeError('boom')


class CheckWithSettings(BaseCheck):
    settings_prefix = 'TRAP'
    defaults = {
        'FIELD_NAME': 'website',
        'TIMEOUT': 30,
    }


class CheckWithNoDefaults(BaseCheck):
    settings_prefix = 'CUSTOM'
    defaults = {}


class CheckWithFields(BaseCheck):
    def get_fields(self):
        return {'honeypot': 'fake-field-object'}


class CheckWithMedia(BaseCheck):
    def get_media(self):
        return Media(js=['formguard/challenge.js'])


class CheckWithTestData(BaseCheck):
    def test_data(self):
        return {'honeypot': ''}

    def check(self, request, form):
        return False


def not_a_check():
    pass


# -- Tests --


class BaseCheckInterfaceTests(SimpleTestCase):
    # get_fields returns empty dict by default
    def test_default_get_fields(self):
        check = BaseCheck()
        assert check.get_fields() == {}

    # get_media returns empty Media by default
    def test_default_get_media(self):
        check = BaseCheck()
        media = check.get_media()
        assert isinstance(media, Media)
        assert list(media.render_js()) == []
        assert list(media.render_css()) == []

    # check() raises NotImplementedError
    def test_check_raises_not_implemented(self):
        check = BaseCheck()
        with pytest.raises(NotImplementedError):
            check.check(None, None)

    # test_data returns empty dict by default
    def test_default_test_data(self):
        check = BaseCheck()
        assert check.test_data() == {}

    # fail_open defaults to True
    def test_default_fail_open(self):
        assert BaseCheck.fail_open is True

    # subclass can override get_fields
    def test_subclass_get_fields(self):
        check = CheckWithFields()
        assert check.get_fields() == {'honeypot': 'fake-field-object'}

    # subclass can override get_media
    def test_subclass_get_media(self):
        check = CheckWithMedia()
        media = check.get_media()
        assert 'formguard/challenge.js' in media._js

    # subclass can override test_data
    def test_subclass_test_data(self):
        check = CheckWithTestData()
        assert check.test_data() == {'honeypot': ''}


class CheckScopedSettingsTests(SimpleTestCase):
    # get_setting falls back to defaults
    def test_falls_back_to_defaults(self):
        check = CheckWithSettings()
        assert check.get_setting('FIELD_NAME') == 'website'
        assert check.get_setting('TIMEOUT') == 30

    # get_setting reads Django settings with prefix
    @override_settings(FORMGUARD_TRAP_FIELD_NAME='phone')
    def test_reads_django_setting(self):
        check = CheckWithSettings()
        assert check.get_setting('FIELD_NAME') == 'phone'

    # Django setting overrides default
    @override_settings(FORMGUARD_TRAP_TIMEOUT=60)
    def test_django_override_wins(self):
        check = CheckWithSettings()
        assert check.get_setting('TIMEOUT') == 60

    # raises ImproperlyConfigured when no default and no setting
    def test_raises_when_missing(self):
        check = CheckWithNoDefaults()
        with pytest.raises(ImproperlyConfigured):
            check.get_setting('NONEXISTENT')

    # falsy Django setting values are returned (not treated as missing)
    @override_settings(FORMGUARD_TRAP_TIMEOUT=0)
    def test_falsy_value_respected(self):
        check = CheckWithSettings()
        assert check.get_setting('TIMEOUT') == 0

    # check with empty settings_prefix uses bare FORMGUARD_ prefix
    @override_settings(FORMGUARD_SOME_VALUE='hello')
    def test_empty_prefix(self):
        check = BaseCheck()
        assert check.get_setting('SOME_VALUE') == 'hello'


class GetChecksTests(SimpleTestCase):
    # imports and instantiates valid check classes
    @override_settings(FORMGUARD_CHECKS=['formguard.tests.test_checks.PassingCheck'])
    def test_valid_check(self):
        checks = get_checks()
        assert len(checks) == 1
        assert isinstance(checks[0], PassingCheck)

    # multiple checks are returned in order
    @override_settings(
        FORMGUARD_CHECKS=[
            'formguard.tests.test_checks.PassingCheck',
            'formguard.tests.test_checks.FailingCheck',
        ]
    )
    def test_multiple_checks(self):
        checks = get_checks()
        assert len(checks) == 2
        assert isinstance(checks[0], PassingCheck)
        assert isinstance(checks[1], FailingCheck)

    # raises ImproperlyConfigured on bad import path
    @override_settings(FORMGUARD_CHECKS=['formguard.does_not_exist.FakeCheck'])
    def test_bad_import(self):
        with pytest.raises(ImproperlyConfigured, match='Could not import'):
            get_checks()

    # raises ImproperlyConfigured when path points to non-BaseCheck
    @override_settings(FORMGUARD_CHECKS=['formguard.tests.test_checks.not_a_check'])
    def test_not_a_subclass(self):
        with pytest.raises(ImproperlyConfigured, match='not a BaseCheck subclass'):
            get_checks()

    # empty check list returns empty list
    @override_settings(FORMGUARD_CHECKS=[])
    def test_empty_checks(self):
        checks = get_checks()
        assert checks == []


class RunChecksTests(SimpleTestCase):
    def _make_form(self, checks):
        form = MagicMock()
        form._checks = checks
        return form

    def _make_request(self):
        request = MagicMock()
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        return request

    # all checks pass returns empty list
    def test_all_pass(self):
        form = self._make_form([PassingCheck()])
        reasons = run_checks(self._make_request(), form)
        assert reasons == []

    # failing check returns reason string
    def test_failing_check(self):
        form = self._make_form([FailingCheck()])
        reasons = run_checks(self._make_request(), form)
        assert reasons == ['check failed']

    # multiple checks: mix of pass and fail
    def test_mixed_checks(self):
        form = self._make_form([PassingCheck(), FailingCheck(), PassingCheck()])
        reasons = run_checks(self._make_request(), form)
        assert reasons == ['check failed']

    # crashing fail_open check is logged and skipped
    def test_fail_open_exception(self):
        form = self._make_form([CrashingCheck()])
        reasons = run_checks(self._make_request(), form)
        assert reasons == []

    # crashing fail_closed check appends a reason
    def test_fail_closed_exception(self):
        form = self._make_form([CrashingFailClosedCheck()])
        reasons = run_checks(self._make_request(), form)
        assert len(reasons) == 1
        assert reasons[0] == 'check error'

    # fail_open exception does not block other checks
    def test_fail_open_continues(self):
        form = self._make_form([CrashingCheck(), FailingCheck()])
        reasons = run_checks(self._make_request(), form)
        assert reasons == ['check failed']

    # fail_closed exception does not block other checks
    def test_fail_closed_continues(self):
        form = self._make_form([CrashingFailClosedCheck(), PassingCheck()])
        reasons = run_checks(self._make_request(), form)
        assert reasons == ['check error']

    # empty check list returns empty list
    def test_no_checks(self):
        form = self._make_form([])
        reasons = run_checks(self._make_request(), form)
        assert reasons == []


class FieldTrapCheckTests(SimpleTestCase):
    def _make_form(self, data):
        form = MagicMock()
        form.cleaned_data = data
        return form

    # get_fields returns a CharField with HoneypotWidget using default name
    def test_get_fields_default(self):
        check = FieldTrapCheck()
        fields = check.get_fields()
        assert 'website' in fields
        field = fields['website']
        assert isinstance(field, CharField)
        assert not field.required
        assert isinstance(field.widget, HoneypotWidget)

    # get_fields uses custom field name from settings
    @override_settings(FORMGUARD_FIELD_TRAP_FIELD_NAME='phone')
    def test_get_fields_custom_name(self):
        check = FieldTrapCheck()
        fields = check.get_fields()
        assert 'phone' in fields
        assert 'website' not in fields

    # check passes when honeypot field is empty
    def test_check_passes_empty(self):
        check = FieldTrapCheck()
        form = self._make_form({'website': ''})
        assert check.check(None, form) is False

    # check triggers when honeypot field is filled
    def test_check_triggers_filled(self):
        check = FieldTrapCheck()
        form = self._make_form({'website': 'http://spam.com'})
        assert check.check(None, form) == 'honeypot field filled'

    # check passes when honeypot field is missing from cleaned_data
    def test_check_passes_missing(self):
        check = FieldTrapCheck()
        form = self._make_form({})
        assert check.check(None, form) is False

    # check uses custom field name from settings
    @override_settings(FORMGUARD_FIELD_TRAP_FIELD_NAME='phone')
    def test_check_custom_name(self):
        check = FieldTrapCheck()
        form = self._make_form({'phone': '555-1234'})
        assert check.check(None, form) == 'honeypot field filled'

    # test_data returns empty string for the honeypot field
    def test_test_data(self):
        check = FieldTrapCheck()
        data = check.test_data()
        assert data == {'website': ''}

    # test_data uses custom field name from settings
    @override_settings(FORMGUARD_FIELD_TRAP_FIELD_NAME='phone')
    def test_test_data_custom_name(self):
        check = FieldTrapCheck()
        data = check.test_data()
        assert data == {'phone': ''}


class TokenCheckTests(SimpleTestCase):
    def _make_form(self, data):
        form = MagicMock()
        form.cleaned_data = data
        return form

    # get_fields returns a CharField with HiddenInput and data-fg-token attr
    def test_get_fields(self):
        check = TokenCheck()
        fields = check.get_fields()
        assert 'fg_token' in fields
        field = fields['fg_token']
        assert isinstance(field, CharField)
        assert not field.required
        assert isinstance(field.widget, HiddenInput)
        assert field.widget.attrs.get('data-fg-token') is True

    # check passes with a valid token submitted after MIN_SECONDS
    def test_check_passes_valid_token(self):
        check = TokenCheck()
        token = TokenCheck._make_token(age=60)
        form = self._make_form({'fg_token': token})
        assert check.check(None, form) is False

    # check triggers when submitted too fast
    def test_check_triggers_too_fast(self):
        check = TokenCheck()
        token = TokenCheck._make_token(age=0)
        form = self._make_form({'fg_token': token})
        assert check.check(None, form) == 'submitted too fast'

    # check triggers on tampered token
    def test_check_triggers_tampered(self):
        check = TokenCheck()
        form = self._make_form({'fg_token': 'garbage-token'})
        assert check.check(None, form) == 'invalid or expired token'

    # check triggers on empty token
    def test_check_triggers_empty(self):
        check = TokenCheck()
        form = self._make_form({'fg_token': ''})
        assert check.check(None, form) == 'invalid or expired token'

    # check triggers on expired token (beyond MAX_SECONDS)
    @override_settings(FORMGUARD_TOKEN_MAX_SECONDS=1)
    def test_check_triggers_expired(self):
        check = TokenCheck()
        past = time.time() - 10
        with patch('django.core.signing.time.time', return_value=past):
            token = TokenCheck._make_token(age=0)
        form = self._make_form({'fg_token': token})
        assert check.check(None, form) == 'invalid or expired token'

    # custom MIN_SECONDS setting is respected
    @override_settings(FORMGUARD_TOKEN_MIN_SECONDS=0)
    def test_custom_min_seconds(self):
        check = TokenCheck()
        token = TokenCheck._make_token(age=0)
        form = self._make_form({'fg_token': token})
        assert check.check(None, form) is False

    # test_data returns a valid token that passes the check
    def test_test_data(self):
        check = TokenCheck()
        data = check.test_data()
        assert 'fg_token' in data
        form = self._make_form(data)
        assert check.check(None, form) is False

    # _make_token produces a signed value that can be loaded
    def test_make_token_is_valid(self):
        token = TokenCheck._make_token(age=5)
        loaded = signing.loads(token, salt=SIGNING_SALT, max_age=3600)
        assert isinstance(loaded, float)
        assert time.time() - loaded >= 5


class JsChallengeCheckTests(SimpleTestCase):
    def _make_form(self, data):
        form = MagicMock()
        form.cleaned_data = data
        return form

    # get_fields returns fg_nonce and fg_js fields
    def test_get_fields(self):
        check = JsChallengeCheck()
        fields = check.get_fields()
        assert 'fg_nonce' in fields
        assert 'fg_js' in fields
        assert isinstance(fields['fg_nonce'], CharField)
        assert isinstance(fields['fg_js'], CharField)
        assert fields['fg_nonce'].widget.attrs.get('data-fg-nonce') is True
        assert fields['fg_js'].widget.attrs.get('data-fg-js') is True

    # get_media includes formguard.js
    def test_get_media(self):
        check = JsChallengeCheck()
        media = check.get_media()
        assert 'formguard/formguard.js' in media._js

    # check passes with valid nonce and matching js value
    def test_check_passes_valid(self):
        check = JsChallengeCheck()
        nonce = 'abc123'
        expected = format(sum(ord(c) for c in nonce) & 0xFFFF, 'x')
        form = self._make_form({'fg_nonce': nonce, 'fg_js': expected})
        assert check.check(None, form) is False

    # check triggers when js value is empty
    def test_check_triggers_empty_js(self):
        check = JsChallengeCheck()
        form = self._make_form({'fg_nonce': 'abc123', 'fg_js': ''})
        assert check.check(None, form) == 'js challenge failed'

    # check triggers when nonce is empty
    def test_check_triggers_empty_nonce(self):
        check = JsChallengeCheck()
        form = self._make_form({'fg_nonce': '', 'fg_js': 'abc'})
        assert check.check(None, form) == 'js challenge failed'

    # check triggers when both fields are missing
    def test_check_triggers_missing_fields(self):
        check = JsChallengeCheck()
        form = self._make_form({})
        assert check.check(None, form) == 'js challenge failed'

    # check triggers on mismatched js value
    def test_check_triggers_mismatch(self):
        check = JsChallengeCheck()
        form = self._make_form({'fg_nonce': 'abc123', 'fg_js': 'wrong'})
        assert check.check(None, form) == 'js challenge mismatch'

    # test_data returns valid nonce and matching js value
    def test_test_data(self):
        check = JsChallengeCheck()
        data = check.test_data()
        assert 'fg_nonce' in data
        assert 'fg_js' in data
        form = self._make_form(data)
        assert check.check(None, form) is False

    # test_data produces consistent nonce/js pairs
    def test_test_data_consistency(self):
        check = JsChallengeCheck()
        data = check.test_data()
        nonce = data['fg_nonce']
        expected = format(sum(ord(c) for c in nonce) & 0xFFFF, 'x')
        assert data['fg_js'] == expected

    # _make_nonce returns a 32-character hex string
    def test_make_nonce_format(self):
        nonce = JsChallengeCheck._make_nonce()
        assert len(nonce) == 32
        int(nonce, 16)  # should not raise
