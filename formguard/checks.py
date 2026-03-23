import logging
import secrets
import time

from django.conf import settings
from django.core import signing
from django.core.exceptions import ImproperlyConfigured
from django.forms import CharField, HiddenInput, Media
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from formguard.conf import get_setting
from formguard.results import GuardResult
from formguard.widgets import HoneypotWidget

logger = logging.getLogger('formguard')

_UNSET = object()


class BaseCheck:
    """Base class for formguard checks."""

    fail_open = False
    message = _('Something went wrong. Please try again.')
    settings_prefix = ''
    defaults = {}

    def __init__(self, options=None):
        self.options = options or {}

    def get_fields(self):
        """Return form fields to inject, as a dict of {name: field}."""
        return {}

    def get_media(self):
        """Return extra media (JS/CSS) required by this check."""
        return Media()

    def check(self, form):
        """Run the check. Return a reason string if triggered, False otherwise."""
        raise NotImplementedError

    def test_data(self):
        """Return form data that will pass this check in tests."""
        return {}

    def get_setting(self, name):
        """Read a check-scoped setting, checking options first, then Django settings, then defaults."""
        if name in self.options:
            return self.options[name]

        if self.settings_prefix:
            setting_name = f'FORMGUARD_{self.settings_prefix}_{name}'
        else:
            setting_name = f'FORMGUARD_{name}'

        value = getattr(settings, setting_name, _UNSET)
        if value is not _UNSET:
            return value

        if name in self.defaults:
            return self.defaults[name]

        raise ImproperlyConfigured(f'{setting_name} is not configured and has no default')


SIGNING_SALT = 'formguard'


class FieldTrapCheck(BaseCheck):
    """Hidden honeypot field that should always be empty. Bots that fill all visible fields get caught."""

    fail_open = True
    settings_prefix = 'FIELD_TRAP'
    defaults = {'FIELD_NAME': 'website'}

    def get_fields(self):
        field_name = self.get_setting('FIELD_NAME')
        return {
            field_name: CharField(
                required=False,
                widget=HoneypotWidget(label=field_name.title()),
            ),
        }

    def check(self, form):
        field_name = self.get_setting('FIELD_NAME')
        if form.cleaned_data.get(field_name, ''):
            return 'honeypot field filled'
        return False

    def test_data(self):
        return {self.get_setting('FIELD_NAME'): ''}


class TokenCheck(BaseCheck):
    """Signed timestamp that records when the form was loaded.

    Catches submissions faster than MIN_SECONDS or with tampered/expired tokens.
    """

    fail_open = True
    settings_prefix = 'TOKEN'
    defaults = {'MIN_SECONDS': 3, 'MAX_SECONDS': 3600}

    def get_fields(self):
        return {
            'fg_token': CharField(
                required=False,
                widget=HiddenInput(attrs={'data-fg-token': True}),
                initial=self._make_token,
            ),
        }

    def check(self, form):
        min_seconds = self.get_setting('MIN_SECONDS')
        max_seconds = self.get_setting('MAX_SECONDS')
        token_value = form.cleaned_data.get('fg_token', '')
        try:
            loaded = signing.loads(token_value, salt=SIGNING_SALT, max_age=max_seconds)
            if time.time() - loaded < min_seconds:
                return 'submitted too fast'
        except (signing.BadSignature, signing.SignatureExpired, TypeError):
            return 'invalid or expired token'
        return False

    def test_data(self):
        return {'fg_token': self._make_token(age=60)}

    @staticmethod
    def _make_token(age=0):
        return signing.dumps(time.time() - age, salt=SIGNING_SALT)


class JsChallengeCheck(BaseCheck):
    """Embed a random nonce in the form. JavaScript computes a value from it that bots without JS can't produce."""

    fail_open = True

    def get_fields(self):
        return {
            'fg_nonce': CharField(
                required=False,
                widget=HiddenInput(attrs={'data-fg-nonce': True}),
                initial=self._make_nonce,
            ),
            'fg_js': CharField(
                required=False,
                widget=HiddenInput(attrs={'data-fg-js': True}),
                initial='',
            ),
        }

    def get_media(self):
        return Media(js=('formguard/formguard.js',))

    def check(self, form):
        nonce_value = form.cleaned_data.get('fg_nonce', '')
        js_value = form.cleaned_data.get('fg_js', '')
        if not js_value or not nonce_value:
            return 'js challenge failed'
        expected = sum(ord(c) for c in nonce_value) & 0xFFFF
        if js_value != format(expected, 'x'):
            return 'js challenge mismatch'
        return False

    def test_data(self):
        nonce = self._make_nonce()
        js_value = format(sum(ord(c) for c in nonce) & 0xFFFF, 'x')
        return {'fg_nonce': nonce, 'fg_js': js_value}

    @staticmethod
    def _make_nonce():
        return secrets.token_hex(16)


class InteractionCheck(BaseCheck):
    """Detect real user interaction via keydown, focusin, and pointerdown events. Accessible to screen readers."""

    fail_open = True

    def get_fields(self):
        return {
            'fg_ia': CharField(
                required=False,
                widget=HiddenInput(attrs={'data-fg-ia': True}),
                initial='',
            ),
        }

    def get_media(self):
        return Media(js=('formguard/formguard-ia.js',))

    def check(self, form):
        if not form.cleaned_data.get('fg_ia'):
            return 'no interaction detected'
        return False

    def test_data(self):
        return {'fg_ia': '1'}


def resolve_checks(check_paths, check_options=None):
    """Import and instantiate check classes from a list of dotted paths."""
    checks = []

    for path in check_paths:
        try:
            cls = import_string(path)
        except ImportError as e:
            raise ImproperlyConfigured(f'Could not import formguard check {path!r}: {e}') from e

        if not (isinstance(cls, type) and issubclass(cls, BaseCheck)):
            raise ImproperlyConfigured(f'{path!r} is not a BaseCheck subclass')

        options = (check_options or {}).get(path, {})
        checks.append(cls(options=options))

    return checks


def get_checks():
    """Import and instantiate check classes from the global FORMGUARD_CHECKS setting."""
    return resolve_checks(get_setting('CHECKS'))


def run_checks(form):
    """Run all checks attached to the form. Return list of GuardResult objects."""
    results = []

    for check in form._checks:
        try:
            reason = check.check(form)
            if reason:
                results.append(GuardResult(check=check, reason=reason, passed=False))
            else:
                results.append(GuardResult(check=check, passed=True))
        except Exception:
            if check.fail_open:
                logger.exception(
                    'formguard check %s.%s raised an exception, skipping',
                    type(check).__module__,
                    type(check).__qualname__,
                )
                results.append(GuardResult(check=check, passed=True))
            else:
                logger.exception(
                    'formguard check %s.%s raised an exception, failing closed',
                    type(check).__module__,
                    type(check).__qualname__,
                )
                results.append(
                    GuardResult(
                        check=check,
                        reason='check error',
                        passed=False,
                    )
                )

    return results
