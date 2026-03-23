# Writing Custom Checks

FormGuard's check pipeline is extensible. Each check is a subclass of
`BaseCheck` that declares its own form fields, media, settings, and
validation logic.

## Basic Example

```python
# myapp/checks.py
from formguard.checks import BaseCheck


class RateLimitCheck(BaseCheck):
    message = 'Too many submissions. Please wait and try again.'

    def check(self, form):
        ip = form.request.META.get('REMOTE_ADDR')
        if is_rate_limited(ip):
            return 'rate limited'
        return False
```

Register it globally in settings:

```python
from formguard.conf import BUILTINS
FORMGUARD_CHECKS = BUILTINS + [
    'myapp.checks.RateLimitCheck',
]
```

Or apply it to a specific form with `guard_checks`:

```python
class ContactForm(GuardedFormMixin, forms.Form):
    guard_checks = [
        'formguard.checks.FieldTrapCheck',
        'myapp.checks.RateLimitCheck',
    ]
    name = forms.CharField()
```

## BaseCheck Interface

Every check can override these methods:

| Method | Default | Purpose |
|---|---|---|
| `check(form)` | `NotImplementedError` | Return `False` if clean, or a reason string if triggered. Access `form.request` for the current request. |
| `get_fields()` | `{}` | Return `{name: Field}` dict of form fields this check needs |
| `get_media()` | `Media()` | Return extra CSS/JS this check needs (beyond widget media) |
| `test_data()` | `{}` | Return valid POST data for this check's fields (used by test helpers) |
| `get_setting(name)` | -- | Read a check-scoped Django setting with fallback to defaults |

And these class attributes:

| Attribute | Default | Purpose |
|---|---|---|
| `fail_open` | `False` | If `True`, exceptions in `check()` are logged and skipped. If `False`, exceptions count as triggered. |
| `message` | `'Something went wrong. Please try again.'` | User-facing error message added to `form.errors` when this check triggers. |
| `settings_prefix` | `''` | Prefix for Django settings lookup (e.g. `'MYCHECK'` reads `FORMGUARD_MYCHECK_*`) |
| `defaults` | `{}` | Default values for check-scoped settings |

## Adding Form Fields

Checks that need user-visible widgets (e.g. CAPTCHA) or hidden fields declare
them via `get_fields()`. The form mixin aggregates fields from all active checks
automatically.

```python
from django import forms
from formguard.checks import BaseCheck


class SecretWordCheck(BaseCheck):
    settings_prefix = 'SECRET_WORD'
    defaults = {'ANSWER': 'swordfish'}
    message = 'Incorrect secret word.'

    def get_fields(self):
        return {
            'secret_word': forms.CharField(required=False),
        }

    def check(self, form):
        answer = self.get_setting('ANSWER')
        if form.cleaned_data.get('secret_word', '') != answer:
            return 'wrong secret word'
        return False

    def test_data(self):
        return {'secret_word': self.get_setting('ANSWER')}
```

For a real-world example with an external widget, server-side verification,
and test key support, see [Cloudflare Turnstile](turnstile.md).

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

    def check(self, form):
        threshold = self.get_setting('THRESHOLD')  # reads FORMGUARD_MYCHECK_THRESHOLD
        api_key = self.get_setting('API_KEY')       # reads FORMGUARD_MYCHECK_API_KEY
        ...
```

## Fail Modes

By default, checks fail closed: if `check()` raises an exception, it's logged
and the submission is blocked. Set `fail_open = True` for checks where a failure
should not block real users (e.g. the built-in honeypot and timing checks).

The built-in checks (`FieldTrapCheck`, `TokenCheck`, `JsChallengeCheck`,
`InteractionCheck`) all set `fail_open = True` because they are invisible to
users and should never block a legitimate submission.

## Testing

See [testing.md](testing.md) for test helpers and how `test_data()` integrates
with `guard_data()`.
