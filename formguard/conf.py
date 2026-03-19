from django.conf import settings

DEFAULTS = {
    'FIELD_NAME': 'website',
    'MIN_SECONDS': 3,
    'MAX_SECONDS': 3600,
    'SUCCESS_MESSAGE': None,
    'CHECKS': [
        'formguard.checks.field_trap',
        'formguard.checks.timing',
        'formguard.checks.signature',
        'formguard.checks.js_challenge',
    ],
}

# Internal constants (not user-configurable)
TOKEN_FIELD_NAME = 'fg_token'
JS_FIELD_NAME = 'fg_js'
SIGNING_SALT = 'formguard'


def get_setting(name):
    return getattr(settings, f'FORMGUARD_{name}', DEFAULTS[name])
