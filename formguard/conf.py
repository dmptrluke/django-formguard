from django.conf import settings

DEFAULTS = {
    'SUCCESS_MESSAGE': None,
    'CHECKS': [
        'formguard.checks.FieldTrapCheck',
        'formguard.checks.TokenCheck',
        'formguard.checks.JsChallengeCheck',
    ],
}


def get_setting(name):
    """Read a global formguard setting."""
    return getattr(settings, f'FORMGUARD_{name}', DEFAULTS[name])
