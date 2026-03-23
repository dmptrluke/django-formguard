import json
from unittest.mock import MagicMock, patch

from django.core.exceptions import ImproperlyConfigured
from django.forms import CharField
from django.test import SimpleTestCase, override_settings

from formguard.contrib.turnstile.checks import (
    TURNSTILE_VERIFY_URL,
    TurnstileCheck,
    verify_token,
)
from formguard.contrib.turnstile.widgets import TurnstileWidget

# -- Widget tests --


class TurnstileWidgetTests(SimpleTestCase):
    # renders the cf-turnstile div with data-sitekey
    def test_renders_sitekey(self):
        widget = TurnstileWidget(site_key='test-key')
        html = widget.render('cf-turnstile-response', '', attrs={'id': 'id_cf'})
        assert 'data-sitekey="test-key"' in html

    # renders data-theme attribute
    def test_renders_theme(self):
        widget = TurnstileWidget(site_key='k', theme='dark')
        html = widget.render('cf-turnstile-response', '', attrs={'id': 'id_cf'})
        assert 'data-theme="dark"' in html

    # renders data-size attribute
    def test_renders_size(self):
        widget = TurnstileWidget(site_key='k', size='compact')
        html = widget.render('cf-turnstile-response', '', attrs={'id': 'id_cf'})
        assert 'data-size="compact"' in html

    # default theme is auto, default size is normal
    def test_default_attrs(self):
        widget = TurnstileWidget(site_key='k')
        html = widget.render('cf-turnstile-response', '', attrs={'id': 'id_cf'})
        assert 'data-theme="auto"' in html
        assert 'data-size="normal"' in html

    # renders the cf-turnstile class on the container div
    def test_renders_container_class(self):
        widget = TurnstileWidget(site_key='k')
        html = widget.render('cf-turnstile-response', '', attrs={'id': 'id_cf'})
        assert 'class="cf-turnstile"' in html

    # value_from_datadict reads cf-turnstile-response from POST data
    def test_value_from_datadict(self):
        widget = TurnstileWidget(site_key='k')
        data = {'cf-turnstile-response': 'some-token'}
        assert widget.value_from_datadict(data, {}, 'ignored-name') == 'some-token'

    # value_from_datadict returns empty string when key is missing
    def test_value_from_datadict_missing(self):
        widget = TurnstileWidget(site_key='k')
        assert widget.value_from_datadict({}, {}, 'ignored') == ''

    # uses the correct template
    def test_template_name(self):
        widget = TurnstileWidget(site_key='k')
        assert widget.template_name == 'formguard/contrib/turnstile/widget.html'


# -- verify_token tests --


class VerifyTokenTests(SimpleTestCase):
    # test key bypass: always-pass key returns True
    def test_bypass_pass(self):
        assert verify_token('any-token', '1x0000000000000000000000000000000AA') is True

    # test key bypass: always-fail key returns False
    def test_bypass_fail(self):
        assert verify_token('any-token', '2x0000000000000000000000000000000AA') is False

    # test key bypass: force-challenge key returns False
    def test_bypass_challenge(self):
        assert verify_token('any-token', '3x0000000000000000000000000000000AA') is False

    # real HTTP path: successful verification
    @patch('formguard.contrib.turnstile.checks.urllib.request.urlopen')
    def test_http_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({'success': True}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        assert verify_token('tok', 'real-secret-key') is True

    # real HTTP path: failed verification
    @patch('formguard.contrib.turnstile.checks.urllib.request.urlopen')
    def test_http_failure(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({'success': False}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        assert verify_token('tok', 'real-secret-key') is False

    # IP is included in the payload when provided
    @patch('formguard.contrib.turnstile.checks.urllib.request.urlopen')
    def test_ip_in_payload(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({'success': True}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        verify_token('tok', 'real-secret', ip='1.2.3.4')

        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        assert b'remoteip=1.2.3.4' in req.data

    # IP is omitted from payload when None
    @patch('formguard.contrib.turnstile.checks.urllib.request.urlopen')
    def test_no_ip_in_payload(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({'success': True}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        verify_token('tok', 'real-secret', ip=None)

        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        assert b'remoteip' not in req.data

    # payload always includes secret and response
    @patch('formguard.contrib.turnstile.checks.urllib.request.urlopen')
    def test_payload_fields(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({'success': True}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        verify_token('my-token', 'my-secret')

        req = mock_urlopen.call_args[0][0]
        assert req.full_url == TURNSTILE_VERIFY_URL
        assert b'secret=my-secret' in req.data
        assert b'response=my-token' in req.data

    # timeout is passed to urlopen
    @patch('formguard.contrib.turnstile.checks.urllib.request.urlopen')
    def test_timeout_passed(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({'success': True}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        verify_token('tok', 'real-secret', timeout=7)

        assert mock_urlopen.call_args[1]['timeout'] == 7

    # non-test key starting with 1x- is not bypassed
    @patch('formguard.contrib.turnstile.checks.urllib.request.urlopen')
    def test_unknown_key_not_bypassed(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({'success': True}).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        verify_token('tok', '1x-not-a-real-test-key')

        mock_urlopen.assert_called_once()


# -- TurnstileCheck tests --


class TurnstileCheckTests(SimpleTestCase):
    def _make_form(self, data, meta=None):
        form = MagicMock()
        form.cleaned_data = data
        form.request = MagicMock()
        form.request.META = meta or {}
        return form

    # fail_open is False (CAPTCHA failure blocks submission)
    def test_fail_open_is_false(self):
        assert TurnstileCheck.fail_open is False

    # message is the expected user-facing string
    def test_message(self):
        check = TurnstileCheck()
        assert str(check.message) == 'Please complete the verification.'

    # check returns reason when token is empty
    def test_empty_token(self):
        check = TurnstileCheck()
        form = self._make_form({'cf-turnstile-response': ''})
        assert check.check(form) == 'turnstile not completed'

    # check returns reason when token field is missing
    def test_missing_token(self):
        check = TurnstileCheck()
        form = self._make_form({})
        assert check.check(form) == 'turnstile not completed'

    # check passes with test key bypass (always-pass)
    @override_settings(FORMGUARD_TURNSTILE_SECRET_KEY='1x0000000000000000000000000000000AA')
    def test_bypass_pass(self):
        check = TurnstileCheck()
        form = self._make_form({'cf-turnstile-response': 'test-token'})
        assert check.check(form) is False

    # check fails with test key bypass (always-fail)
    @override_settings(FORMGUARD_TURNSTILE_SECRET_KEY='2x0000000000000000000000000000000AA')
    def test_bypass_fail(self):
        check = TurnstileCheck()
        form = self._make_form({'cf-turnstile-response': 'test-token'})
        assert check.check(form) == 'turnstile verification failed'

    # get_fields returns cf-turnstile-response CharField
    def test_get_fields(self):
        check = TurnstileCheck()
        fields = check.get_fields()
        assert 'cf-turnstile-response' in fields
        field = fields['cf-turnstile-response']
        assert isinstance(field, CharField)
        assert not field.required
        assert isinstance(field.widget, TurnstileWidget)

    # get_fields widget has the configured site key
    def test_get_fields_site_key(self):
        check = TurnstileCheck()
        fields = check.get_fields()
        widget = fields['cf-turnstile-response'].widget
        assert widget.site_key == '1x00000000000000000000AA'

    # get_fields widget uses theme and size from settings
    @override_settings(FORMGUARD_TURNSTILE_THEME='dark', FORMGUARD_TURNSTILE_SIZE='compact')
    def test_get_fields_theme_size(self):
        check = TurnstileCheck()
        fields = check.get_fields()
        widget = fields['cf-turnstile-response'].widget
        assert widget.theme == 'dark'
        assert widget.size == 'compact'

    # get_media includes Cloudflare script
    def test_get_media(self):
        check = TurnstileCheck()
        media = check.get_media()
        assert 'https://challenges.cloudflare.com/turnstile/v0/api.js' in media._js

    # test_data returns valid data dict
    def test_test_data(self):
        check = TurnstileCheck()
        data = check.test_data()
        assert data == {'cf-turnstile-response': 'test-token'}

    # test_data produces data that passes with test key bypass
    def test_test_data_passes_check(self):
        check = TurnstileCheck()
        data = check.test_data()
        form = self._make_form(data)
        assert check.check(form) is False

    # missing SITE_KEY raises ImproperlyConfigured
    @override_settings()
    def test_missing_site_key(self):
        # Remove the test setting to trigger the error
        from django.conf import settings

        if hasattr(settings, 'FORMGUARD_TURNSTILE_SITE_KEY'):
            delattr(settings, 'FORMGUARD_TURNSTILE_SITE_KEY')
        check = TurnstileCheck()
        with self.assertRaises(ImproperlyConfigured):
            check.get_setting('SITE_KEY')

    # missing SECRET_KEY raises ImproperlyConfigured
    @override_settings()
    def test_missing_secret_key(self):
        from django.conf import settings

        if hasattr(settings, 'FORMGUARD_TURNSTILE_SECRET_KEY'):
            delattr(settings, 'FORMGUARD_TURNSTILE_SECRET_KEY')
        check = TurnstileCheck()
        with self.assertRaises(ImproperlyConfigured):
            check.get_setting('SECRET_KEY')


# -- Client IP extraction tests --


class ClientIpTests(SimpleTestCase):
    def _make_check_and_request(self, ip_header, meta=None):
        check = TurnstileCheck()
        request = MagicMock()
        request.META = meta or {}
        with override_settings(FORMGUARD_TURNSTILE_IP_HEADER=ip_header):
            return check._get_client_ip(request)

    # returns None when IP_HEADER is None
    def test_no_header(self):
        result = self._make_check_and_request(None)
        assert result is None

    # reads REMOTE_ADDR from request.META
    def test_remote_addr(self):
        result = self._make_check_and_request('REMOTE_ADDR', meta={'REMOTE_ADDR': '10.0.0.1'})
        assert result == '10.0.0.1'

    # takes leftmost IP from comma-separated X-Forwarded-For
    def test_forwarded_for_comma_separated(self):
        result = self._make_check_and_request(
            'HTTP_X_FORWARDED_FOR',
            meta={'HTTP_X_FORWARDED_FOR': '1.2.3.4, 10.0.0.1, 172.16.0.1'},
        )
        assert result == '1.2.3.4'

    # returns None when header is present but empty
    def test_empty_header_value(self):
        result = self._make_check_and_request('HTTP_X_FORWARDED_FOR', meta={'HTTP_X_FORWARDED_FOR': ''})
        assert result is None

    # returns None when header is absent from META
    def test_missing_header(self):
        result = self._make_check_and_request('HTTP_CF_CONNECTING_IP', meta={})
        assert result is None
