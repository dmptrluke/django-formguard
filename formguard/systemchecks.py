from django.conf import settings
from django.core.checks import Error, Warning
from django.utils.module_loading import import_string

from formguard.checks import BaseCheck


def check_settings(**kwargs):
    """Validate FORMGUARD_CHECKS in Django settings at startup."""
    errors = []

    if not hasattr(settings, 'FORMGUARD_CHECKS'):
        return errors

    checks_value = settings.FORMGUARD_CHECKS

    if not isinstance(checks_value, (list, tuple)):
        errors.append(Error(
            'FORMGUARD_CHECKS should be a list or tuple of dotted paths.',
            id='formguard.E001',
        ))
        return errors

    if len(checks_value) == 0:
        errors.append(Warning(
            'FORMGUARD_CHECKS is empty. No forms will be protected '
            'unless they define guard_checks.',
            id='formguard.W001',
        ))
        return errors

    valid_classes = []
    has_import_errors = False

    for path in checks_value:
        try:
            cls = import_string(path)
        except ImportError as e:
            errors.append(Error(
                f'FORMGUARD_CHECKS contains {path!r} which could not be '
                f'imported: {e}',
                id='formguard.E002',
            ))
            has_import_errors = True
            continue

        if not (isinstance(cls, type) and issubclass(cls, BaseCheck)):
            errors.append(Error(
                f'FORMGUARD_CHECKS contains {path!r} which is not a '
                f'BaseCheck subclass.',
                id='formguard.E003',
            ))
            has_import_errors = True
            continue

        valid_classes.append((path, cls))

    if has_import_errors:
        return errors

    field_owners = {}
    for path, cls in valid_classes:
        instance = cls()
        for name in instance.get_fields():
            if name in field_owners:
                errors.append(Error(
                    f'Checks {field_owners[name]} and {cls.__name__} both '
                    f'define field {name!r}.',
                    id='formguard.E004',
                ))
            else:
                field_owners[name] = cls.__name__

    return errors
