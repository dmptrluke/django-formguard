from django.conf import settings

__all__ = ['BUILTINS', 'DEFAULTS', 'default_checks', 'get_config']

BUILTINS = [
    'formguard.checks.FieldTrapCheck',
    'formguard.checks.TokenCheck',
    'formguard.checks.JsChallengeCheck',
    'formguard.checks.InteractionCheck',
]

DEFAULTS = {
    'CHECKS': BUILTINS,
}


def default_checks(include=None, exclude=None):
    """Return the configured check list, optionally adding or removing checks."""
    checks = list(get_config('CHECKS'))
    if exclude:
        checks = [c for c in checks if c not in exclude]
    if include:
        checks.extend(include)
    return checks


def get_config(name):
    """Read a global formguard setting."""
    return getattr(settings, f'FORMGUARD_{name}', DEFAULTS[name])
