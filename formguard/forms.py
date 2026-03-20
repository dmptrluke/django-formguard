from django.core.exceptions import ImproperlyConfigured

from formguard.checks import get_checks, resolve_checks


class GuardedFormMixin:
    """Aggregate fields and media from all configured checks."""

    formguard_checks = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.formguard_checks is not None:
            self._checks = resolve_checks(self.formguard_checks)
        else:
            self._checks = get_checks()
        seen_fields = {}

        for check in self._checks:
            for name, field in check.get_fields().items():
                if name in self.fields:
                    raise ImproperlyConfigured(
                        f"Check {check.__class__.__name__} adds field '{name}' "
                        f'which conflicts with an existing form field.'
                    )
                if name in seen_fields:
                    raise ImproperlyConfigured(
                        f"Check {check.__class__.__name__} adds field '{name}' "
                        f'which is already added by {seen_fields[name]}.'
                    )
                seen_fields[name] = check.__class__.__name__
                self.fields[name] = field

    @property
    def media(self):
        base = super().media
        for check in self._checks:
            base += check.get_media()
        return base
