# django-formguard

Invisible form protection for Django. A pluggable check pipeline that catches
bots without any user interaction.

**WARNING**: This library is still under development. Expect breaking changes until 1.0.0.

## How It Works

FormGuard runs a series of checks against each form submission:

1. **Field trap** - hidden honeypot field that bots fill in
2. **Token** - signed timestamp that catches fast or tampered submissions
3. **JS challenge** - nonce computation that requires JavaScript execution
4. **Interaction proof** - detects real user input (accessible to screen readers)

All checks are invisible to real users. Check failures are handled as standard
form validation errors, with customizable failure handling for honeypot-style
silent rejection.

FormGuard is extensible - new checks can be added easily. See [Custom Checks](docs/custom-checks.md).

## Installation

```bash
pip install django-formguard
```

Add `'formguard'` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'formguard',
]
```

## Quick Start

### 1. Set up your form
Add `GuardedFormMixin` to your form.

```python
from django import forms
from formguard.conf import default_checks
from formguard.forms import GuardedFormMixin

class ContactForm(GuardedFormMixin, forms.Form):
    guard_checks = default_checks(exclude=['formguard.checks.InteractionCheck'])

    name = forms.CharField()
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
```

`default_checks()` returns the built-in check list. Use `include` and `exclude`
to customize it, or omit `guard_checks` entirely to use all defaults.

### 2. Set up your template

Include `{{ form.media }}` in your `<head>` so the honeypot CSS and JS
checks load. 

```html
<head>
    {{ form.media }}
</head>
<body>
    <form method="post">
        {% csrf_token %}
        {{ form }}
        <button type="submit">Send</button>
    </form>
</body>
```

If you render fields manually, include
`{{ form.guard_fields }}` to add the FormGuard fields.

### 3. Check submissions in your view

Guard checks run inside `is_valid()`, so your view uses standard Django patterns.

**Class-based views** - use `GuardedFormViewMixin`:

```python
from django.views.generic import FormView
from formguard.views import GuardedFormViewMixin

class ContactView(GuardedFormViewMixin, FormView):
    form_class = ContactForm
    template_name = 'contact.html'
    success_url = '/thanks/'

    def form_valid(self, form):
        send_email(form.cleaned_data)
        return super().form_valid(form)
```

If a check fails, the form returns an error message. To silently redirect bots
to a fake success page instead, see [Failure Handling](docs/failure-handling.md).

**Function-based views** - see [Function-Based Views](docs/function-based-views.md)

## Settings

All settings are optional. Defaults work out of the box. All four built-in
checks are enabled by default.

```python
# add a custom check alongside the builtins
from formguard.conf import BUILTINS
FORMGUARD_CHECKS = BUILTINS + [
    'myapp.checks.TurnstileCheck',
]

# tune the built-in checks
FORMGUARD_FIELD_TRAP_FIELD_NAME = 'website'  # default
FORMGUARD_TOKEN_MIN_SECONDS = 3              # default
FORMGUARD_TOKEN_MAX_SECONDS = 3600           # default
```

## Further Reading

- [Function-Based Views](docs/function-based-views.md) - using FormGuard without class-based views
- [Failure Handling](docs/failure-handling.md) - customize what happens when a guard check fails
- [Configuration](docs/configuration.md) - per-form checks, manual rendering, settings reference
- [Built-in Checks](docs/checks.md) - reference for each check
- [Custom Checks](docs/custom-checks.md) - write your own checks (CAPTCHA, rate limiting, etc.)
- [Testing](docs/testing.md) - test helpers for guarded forms
- [Signals](docs/signals.md) - hook into bot detection events

## CSP Compatibility

FormGuard uses external static files for CSS and JS (no inline styles or
scripts), so it works with Content Security Policy out of the box when
`'self'` is in your `script-src` and `style-src`.

For strict nonce-based CSP policies, use
[django-csp-helpers](https://github.com/dmptrluke/django-csp-helpers) to add
nonces to the `{{ form.media }}` output.

## License

This software is released under the MIT license.
```
Copyright (c) 2026 Luke Rogers

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
