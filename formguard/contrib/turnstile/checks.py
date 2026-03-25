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


def verify_token(token, secret_key, ip=None, timeout=5):
    """Verify a Turnstile response token with Cloudflare. Returns True if valid."""
    if secret_key in TURNSTILE_TEST_KEYS:
        return secret_key in TURNSTILE_TEST_KEYS_PASS

    payload = {'secret': secret_key, 'response': token}
    if ip:
        payload['remoteip'] = ip
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(TURNSTILE_VERIFY_URL, data=data)  # noqa: S310
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        return json.loads(resp.read()).get('success', False)


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
        if not verify_token(token, self.get_setting('SECRET_KEY'), ip=ip, timeout=timeout):
            return 'turnstile verification failed'
        return False

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
