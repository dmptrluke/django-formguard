import hashlib
import json
import urllib.parse
import urllib.request

from django.forms import CharField, Media
from django.utils.translation import gettext_lazy as _

from formguard.checks import BaseCheck
from formguard.contrib.turnstile.widgets import TurnstileWidget

TURNSTILE_VERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'

TURNSTILE_TEST_KEYS_PASS = {'1x0000000000000000000000000000000AA'}
TURNSTILE_TEST_KEYS_FAIL = {
    '2x0000000000000000000000000000000AA',
    '3x0000000000000000000000000000000AA',
}
TURNSTILE_TEST_KEYS = TURNSTILE_TEST_KEYS_PASS | TURNSTILE_TEST_KEYS_FAIL


def verify_token(token, secret_key, ip=None, timeout=5, expected_hostname=None, expected_action=None):
    """Verify a Turnstile response token and any configured response metadata."""
    if secret_key in TURNSTILE_TEST_KEYS:
        return secret_key in TURNSTILE_TEST_KEYS_PASS

    payload = {'secret': secret_key, 'response': token}
    if ip:
        payload['remoteip'] = ip
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(TURNSTILE_VERIFY_URL, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        result = json.loads(resp.read())

    if not result.get('success', False):
        return False
    if expected_hostname is not None and result.get('hostname') != expected_hostname:
        return False
    if expected_action is not None and result.get('action') != expected_action:
        return False
    return True


class TurnstileCheck(BaseCheck):
    """Cloudflare Turnstile CAPTCHA verification."""

    fail_open = False
    message = _('Please complete the verification.')
    settings_prefix = 'TURNSTILE'
    defaults = {
        'THEME': 'auto',
        'SIZE': 'normal',
        'APPEARANCE': None,
        'IP_HEADER': None,
        'TIMEOUT': 5,
        'CALLBACK': None,
        'ACTION': 'auto',
        'EXPECTED_HOSTNAME': None,
    }

    def get_fields(self):
        return {
            'cf-turnstile-response': CharField(
                required=False,
                widget=TurnstileWidget(
                    site_key=self.get_setting('SITE_KEY'),
                    theme=self.get_setting('THEME'),
                    size=self.get_setting('SIZE'),
                    appearance=self.get_setting('APPEARANCE'),
                    callback=self.get_setting('CALLBACK'),
                    action=self._get_action(),
                ),
            ),
        }

    def get_media(self):
        return Media(
            js=('https://challenges.cloudflare.com/turnstile/v0/api.js',),
        )

    def check(self, form):
        token = form.cleaned_data.get('cf-turnstile-response', '')
        if not token:
            return 'turnstile not completed'

        ip = self._get_client_ip(form.request)
        timeout = self.get_setting('TIMEOUT')
        if not verify_token(
            token,
            self.get_setting('SECRET_KEY'),
            ip=ip,
            timeout=timeout,
            expected_hostname=self.get_setting('EXPECTED_HOSTNAME'),
            expected_action=self._get_action(form),
        ):
            return 'turnstile verification failed'
        return None

    def _get_action(self, form=None):
        action = self.get_setting('ACTION')
        if action != 'auto':
            return action

        owner_class = type(form) if form is not None else self._owner_class
        if owner_class is None:
            return None

        owner_path = f'{owner_class.__module__}.{owner_class.__qualname__}'
        check_path = f'{type(self).__module__}.{type(self).__qualname__}'
        return hashlib.sha256(f'{owner_path}:{check_path}'.encode()).hexdigest()[:32]

    def _get_client_ip(self, request):
        header = self.get_setting('IP_HEADER')
        if not header:
            return None
        value = request.META.get(header, '')
        if ',' in value:
            return value.split(',')[0].strip()
        return value or None

    def test_data(self):
        return {'cf-turnstile-response': 'test-token'}
