from formguard.checks import get_checks, resolve_checks


class GuardedFormTestMixin:
    """Mixin for TestCase classes that test guarded forms."""

    def guard_data(self, form_class=None, **overrides):
        """Return valid guard POST data, using the form's checks if it defines formguard_checks."""
        if form_class and hasattr(form_class, 'formguard_checks'):
            checks = resolve_checks(form_class.formguard_checks)
        else:
            checks = get_checks()
        data = {}
        for check in checks:
            data.update(check.test_data())
        data.update(overrides)
        return data
