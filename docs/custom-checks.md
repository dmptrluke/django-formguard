# Writing Custom Checks

FormGuard's check pipeline is extensible. Each check is a subclass of
`BaseCheck` that declares its own form fields, media, settings, and
validation logic.

## Basic Example

```python
# myapp/checks.py
from formguard.checks import BaseCheck


class RateLimitCheck(BaseCheck):
    def check(self, request, form):
        ip = request.META.get('REMOTE_ADDR')
        if is_rate_limited(ip):
            return 'rate limited'
        return False
```

Register it globally in settings:

```python
FORMGUARD_CHECKS = [
    'formguard.checks.FieldTrapCheck',
    'formguard.checks.TokenCheck',
    'formguard.checks.JsChallengeCheck',
    'myapp.checks.RateLimitCheck',
]
```

Or apply it to a specific form with `formguard_checks`:

```python
class ContactForm(GuardedFormMixin, forms.Form):
    formguard_checks = [
        'formguard.checks.FieldTrapCheck',
        'myapp.checks.RateLimitCheck',
    ]
    name = forms.CharField()
```

## BaseCheck Interface

Every check can override these methods:

| Method | Default | Purpose |
|---|---|---|
| `check(request, form)` | `NotImplementedError` | Return `False` if clean, or a reason string if triggered |
| `get_fields()` | `{}` | Return `{name: Field}` dict of form fields this check needs |
| `get_media()` | `Media()` | Return extra CSS/JS this check needs (beyond widget media) |
| `test_data()` | `{}` | Return valid POST data for this check's fields (used by test helpers) |
| `get_setting(name)` | -- | Read a check-scoped Django setting with fallback to defaults |

And these class attributes:

| Attribute | Default | Purpose |
|---|---|---|
| `fail_open` | `True` | If `True`, exceptions in `check()` are logged and skipped. If `False`, exceptions count as triggered. |
| `settings_prefix` | `''` | Prefix for Django settings lookup (e.g. `'MYCHECK'` reads `FORMGUARD_MYCHECK_*`) |
| `defaults` | `{}` | Default values for check-scoped settings |

## Adding Form Fields

Checks that need user-visible widgets (e.g. CAPTCHA) or hidden fields declare
them via `get_fields()`. The form mixin aggregates fields from all active checks
automatically.

```python
from django import forms
from formguard.checks import BaseCheck


class TurnstileCheck(BaseCheck):
    settings_prefix = 'TURNSTILE'
    defaults = {
        'SITE_KEY': None,
        'SECRET_KEY': None,
    }
    fail_open = False

    def get_fields(self):
        return {
            'cf-turnstile-response': forms.CharField(
                required=False,
                widget=TurnstileWidget(site_key=self.get_setting('SITE_KEY')),
            ),
        }

    def get_media(self):
        return forms.Media(
            js=('https://challenges.cloudflare.com/turnstile/v0/api.js',),
        )

    def check(self, request, form):
        token = form.cleaned_data.get('cf-turnstile-response', '')
        if not token:
            return 'turnstile not completed'
        if not verify_turnstile(token, self.get_setting('SECRET_KEY')):
            return 'turnstile verification failed'
        return False

    def test_data(self):
        return {'cf-turnstile-response': 'test-token'}
```

Configure via Django settings:

```python
FORMGUARD_TURNSTILE_SITE_KEY = 'your-site-key'
FORMGUARD_TURNSTILE_SECRET_KEY = 'your-secret-key'
```

## Check-Scoped Settings

Each check declares a `settings_prefix` and `defaults` dict.
`self.get_setting('NAME')` looks up `FORMGUARD_{PREFIX}_{NAME}` in Django
settings, falling back to the check's `defaults`. If neither exists, it raises
`ImproperlyConfigured`.

```python
class MyCheck(BaseCheck):
    settings_prefix = 'MYCHECK'
    defaults = {
        'THRESHOLD': 5,
        'API_KEY': None,  # no default -- must be configured
    }

    def check(self, request, form):
        threshold = self.get_setting('THRESHOLD')  # reads FORMGUARD_MYCHECK_THRESHOLD
        api_key = self.get_setting('API_KEY')       # reads FORMGUARD_MYCHECK_API_KEY
        ...
```

## Fail Modes

By default, checks fail open: if `check()` raises an exception, it's logged
and the check is skipped. Set `fail_open = False` for checks where a failure
should block the submission (e.g. a CAPTCHA service being unreachable should
not silently let all bots through).

## Testing

See [testing.md](testing.md) for test helpers and how `test_data()` integrates
with `guard_data()`.
