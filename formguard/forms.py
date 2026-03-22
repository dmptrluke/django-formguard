import logging

from django.core.exceptions import ImproperlyConfigured
from django.utils.safestring import mark_safe

from formguard.checks import get_checks, resolve_checks
from formguard.utils import handle_bot

logger = logging.getLogger('formguard')


class GuardedFormMixin:
    """Aggregate fields and media from all configured checks, and run them during validation."""

    formguard_checks = None

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.guard_failures = []
        self._guard_checks_run = False

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

    def is_valid(self):
        valid = super().is_valid()
        if valid:
            self._run_guard_checks()
            valid = not self.guard_failures
        return valid

    def _run_guard_checks(self):
        if self._guard_checks_run:
            return
        self._guard_checks_run = True

        if self.request is None:
            raise ImproperlyConfigured(
                'GuardedFormMixin requires request=request in the form constructor.'
            )

        for check in self._checks:
            try:
                result = check.check(self)
                if result:
                    self.guard_failures.append(result)
                    self.add_error(None, check.message)
            except Exception:
                if check.fail_open:
                    logger.exception(
                        'formguard check %s.%s raised an exception, skipping',
                        type(check).__module__,
                        type(check).__qualname__,
                    )
                else:
                    logger.exception(
                        'formguard check %s.%s raised an exception, failing closed',
                        type(check).__module__,
                        type(check).__qualname__,
                    )
                    self.guard_failures.append('check error')
                    self.add_error(None, check.message)

        if self.guard_failures:
            handle_bot(self.__class__, self.request, self, self.guard_failures)

    @property
    def guard_fields(self):
        """Render all guard fields as HTML, for templates that render fields manually."""
        output = []
        for check in self._checks:
            for name in check.get_fields():
                output.append(str(self[name]))
        return mark_safe('\n'.join(output))

    @property
    def media(self):
        base = super().media
        for check in self._checks:
            base += check.get_media()
        return base
