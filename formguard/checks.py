import logging
import time

from django.core import signing
from django.utils.module_loading import import_string

from formguard.conf import JS_FIELD_NAME, SIGNING_SALT, TOKEN_FIELD_NAME, get_setting

logger = logging.getLogger('formguard')


def field_trap(request, form):
    """Trigger if the honeypot field has any value (hidden field should always be empty)."""
    field_name = get_setting('FIELD_NAME')
    value = form.cleaned_data.get(field_name, '')
    if value:
        return 'honeypot field filled'
    return False


def timing(request, form):
    """Trigger if the form was submitted faster than MIN_SECONDS after page load."""
    min_seconds = get_setting('MIN_SECONDS')
    max_seconds = get_setting('MAX_SECONDS')
    token_value = form.cleaned_data.get(TOKEN_FIELD_NAME, '')

    try:
        loaded = signing.loads(token_value, salt=SIGNING_SALT, max_age=max_seconds)
        if time.time() - loaded < min_seconds:
            return 'submitted too fast'
    except (signing.BadSignature, signing.SignatureExpired, TypeError):
        return 'invalid or missing token'

    return False


def signature(request, form):
    """Trigger if the signed token is missing, tampered, or expired."""
    max_seconds = get_setting('MAX_SECONDS')
    token_value = form.cleaned_data.get(TOKEN_FIELD_NAME, '')

    try:
        signing.loads(token_value, salt=SIGNING_SALT, max_age=max_seconds)
    except (signing.BadSignature, signing.SignatureExpired, TypeError):
        return 'invalid or expired token'

    return False


def js_challenge(request, form):
    """Trigger if the JS challenge field doesn't match the expected token prefix."""
    token_value = form.cleaned_data.get(TOKEN_FIELD_NAME, '')
    js_value = form.cleaned_data.get(JS_FIELD_NAME, '')

    if not js_value or not token_value:
        return 'js challenge failed'

    expected = sum(ord(c) for c in token_value) & 0xFFFF
    if js_value != format(expected, 'x'):
        return 'js challenge mismatch'

    return False


def run_checks(request, form):
    """Run all configured checks. Return list of reason strings for triggered checks."""
    check_paths = get_setting('CHECKS')
    reasons = []

    for path in check_paths:
        try:
            check_fn = import_string(path)
            result = check_fn(request, form)
            if result:
                reasons.append(result)
        except Exception:
            logger.exception('formguard check %s raised an exception, skipping', path)

    return reasons
