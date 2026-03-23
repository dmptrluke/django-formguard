# Configuration

## Per-Form Checks

By default, all forms use the global `FORMGUARD_CHECKS` setting. To use
different checks on a specific form, set `guard_checks` on the class:

```python
class ContactForm(GuardedFormMixin, forms.Form):
    guard_checks = [
        'formguard.checks.FieldTrapCheck',
        'formguard.checks.TokenCheck',
    ]
    name = forms.CharField()
    message = forms.CharField(widget=forms.Textarea)
```

To start from the defaults and exclude specific checks, use `default_checks()`:

```python
from formguard.conf import default_checks

class LoginForm(GuardedFormMixin, forms.Form):
    guard_checks = default_checks(exclude=['formguard.checks.InteractionCheck'])
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
```

When testing forms with per-form checks, pass the form class to
`guard_data()` so the helper generates data for the right checks:

```python
data = self.guard_data(form_class=ContactForm)
```

## Per-Form Check Options

Override check settings on a specific form with `guard_check_options`. Keys
are dotted check paths, values are dicts of setting overrides. Option keys
match the setting names (uppercase, without the `FORMGUARD_` prefix).

```python
class InterstitialForm(GuardedFormMixin, forms.Form):
    guard_checks = [
        'formguard.contrib.turnstile.TurnstileCheck',
    ]
    guard_check_options = {
        'formguard.contrib.turnstile.TurnstileCheck': {
            'CALLBACK': 'onTurnstileComplete',
        },
    }
```

Options take priority over Django settings and check defaults:

```
guard_check_options -> FORMGUARD_{PREFIX}_{NAME} -> check defaults
```

## Manual Field Rendering

If your template renders fields individually instead of using `{{ form }}`,
use `{{ form.guard_fields }}` to render all guard fields at once:

```html
<form method="post">
    {% csrf_token %}
    {{ form.guard_fields }}
    <label>Name</label>
    {{ form.name }}
    <button type="submit">Send</button>
</form>
```

This renders the honeypot, token, nonce, and JS challenge fields - whatever
the active checks require. It adapts automatically when you change checks.

## Settings Reference

All settings are optional. Defaults work out of the box.

| Setting | Default | Description |
|---------|---------|-------------|
| `FORMGUARD_CHECKS` | All four built-in checks | List of dotted paths to check classes |
| `FORMGUARD_FIELD_TRAP_FIELD_NAME` | `'website'` | HTML field name for the honeypot |
| `FORMGUARD_TOKEN_MIN_SECONDS` | `3` | Minimum seconds before a submission is accepted |
| `FORMGUARD_TOKEN_MAX_SECONDS` | `3600` | Maximum token age before it expires |
