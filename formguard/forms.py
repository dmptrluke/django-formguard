import logging

from django.core.exceptions import ImproperlyConfigured
from django.utils.safestring import mark_safe

from formguard.checks import resolve_checks, run_checks
from formguard.conf import get_setting
from formguard.signals import guard_checked, guard_failed
from formguard.utils import handle_bot

logger = logging.getLogger('formguard')


class GuardedFormMixin:
    """Aggregate fields and media from all configured checks, and run them during validation."""

    guard_checks = None
    guard_check_options = None

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.guard_results = []
        self.guard_failures = []
        self._guard_checks_run = False

        super().__init__(*args, **kwargs)

        if self.guard_checks is not None:
            self._checks = resolve_checks(self.guard_checks, self.guard_check_options)
        else:
            self._checks = resolve_checks(get_setting('CHECKS'), self.guard_check_options)
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
            raise ImproperlyConfigured('GuardedFormMixin requires request=request in the form constructor.')

        self.guard_results = run_checks(self)
        self.guard_failures = [r for r in self.guard_results if not r.passed]

        for failure in self.guard_failures:
            self.add_error(None, failure.check.message)

        if self.guard_failures:
            handle_bot(self.__class__, self.request, self, self.guard_failures)
            guard_failed.send(
                sender=self.__class__,
                request=self.request,
                form=self,
                results=self.guard_results,
            )

        guard_checked.send(
            sender=self.__class__,
            request=self.request,
            form=self,
            results=self.guard_results,
        )

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
