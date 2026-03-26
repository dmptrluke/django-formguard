from formguard.checks import resolve_checks
from formguard.conf import get_config

__all__ = ['GuardedFormTestMixin']


class GuardedFormTestMixin:
    """Mixin for TestCase classes that test guarded forms."""

    def guard_data(self, form_class=None, **overrides):
        """Return valid guard POST data, matching the form's check configuration."""
        if form_class and getattr(form_class, 'guard_checks', None) is not None:
            check_paths = form_class.guard_checks
        else:
            check_paths = get_config('CHECKS')
        options = getattr(form_class, 'guard_check_options', None) if form_class else None
        checks = resolve_checks(check_paths, options)
        data = {}
        for check in checks:
            data.update(check.test_data())
        data.update(overrides)
        return data
