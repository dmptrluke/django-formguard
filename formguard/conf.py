from django.conf import settings

DEFAULTS = {
    'CHECKS': [
        'formguard.checks.FieldTrapCheck',
        'formguard.checks.TokenCheck',
        'formguard.checks.JsChallengeCheck',
        'formguard.checks.InteractionCheck',
    ],
}


def get_setting(name):
    """Read a global formguard setting."""
    return getattr(settings, f'FORMGUARD_{name}', DEFAULTS[name])
