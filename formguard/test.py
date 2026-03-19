import time

from django.core import signing

from formguard.conf import JS_FIELD_NAME, SIGNING_SALT, TOKEN_FIELD_NAME, get_setting


def make_guard_token(age=60):
    """Create a valid guard token that appears to have been generated `age` seconds ago."""
    return signing.dumps(time.time() - age, salt=SIGNING_SALT)


class GuardedFormTestMixin:
    """Mixin for TestCase classes that test guarded forms."""

    def guard_data(self, **overrides):
        """Return a dict with valid guard fields for POST data."""
        token = make_guard_token()
        js_value = format(sum(ord(c) for c in token) & 0xFFFF, 'x')
        data = {
            get_setting('FIELD_NAME'): '',
            TOKEN_FIELD_NAME: token,
            JS_FIELD_NAME: js_value,
        }
        data.update(overrides)
        return data
