# django-formguard

Invisible form protection for Django. A pluggable check pipeline that catches
bots without any user interaction.

## How It Works

FormGuard runs a pipeline of checks against each form submission:

1. **Field trap** - a hidden honeypot field that should always be empty. Bots
   that fill all visible fields get caught.
2. **Token** - a signed timestamp records when the form was loaded. Submissions
   faster than `MIN_SECONDS` or with tampered/expired tokens are flagged.
3. **JS challenge** - a random nonce is embedded in the form. JavaScript
   computes a value from it that bots without JS execution can't produce.

All checks are invisible to real users. Bots receive a fake success response
indistinguishable from a real one.

The pipeline is extensible - each check is a class that owns its form fields,
media, and settings. See [Custom Checks](docs/custom-checks.md).

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

### 1. Define your form

```python
# forms.py
from django import forms
from formguard.forms import GuardedFormMixin

class ContactForm(GuardedFormMixin, forms.Form):
    name = forms.CharField()
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
```

### 2. Include `{{ form.media }}` in your template

FormGuard's CSS and JS are declared as form media. Include `{{ form.media }}`
in your template's `<head>` so the honeypot field is hidden and the JS
challenge runs.

```html
<!-- contact.html -->
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

### 3. Check submissions in your view

**Class-based views** - use `GuardedFormViewMixin`:

```python
from django.views.generic import FormView
from formguard.views import GuardedFormViewMixin

class ContactView(GuardedFormViewMixin, FormView):
    form_class = ContactForm
    template_name = 'contact.html'
    success_url = '/thanks/'

    def form_valid(self, form):
        if self.is_bot(form):
            return self.bot_response()
        send_email(form.cleaned_data)
        return super().form_valid(form)
```

**Function-based views** - use the `@guard_form` decorator:

```python
from formguard.decorators import guard_form

@guard_form(form_class=ContactForm, success_url='/thanks/')
def contact_view(request, form=None):
    # only reached if the form is clean (bots were already redirected)
    send_email(form.cleaned_data)
    return redirect('/thanks/')
```

## Settings

All settings are optional. Defaults work out of the box.

| Setting | Default | Description |
| -- | -- | -- |
| `FORMGUARD_SUCCESS_MESSAGE` | `None` | Fake success message shown to bots (via Django messages) |
| `FORMGUARD_CHECKS` | *(see below)* | Ordered list of check class paths |
| `FORMGUARD_FIELD_TRAP_FIELD_NAME` | `'website'` | Honeypot field name (label derived via `.title()`) |
| `FORMGUARD_TOKEN_MIN_SECONDS` | `3` | Minimum seconds before a submission is accepted |
| `FORMGUARD_TOKEN_MAX_SECONDS` | `3600` | Maximum token age before expiry |

Default checks:

```python
FORMGUARD_CHECKS = [
    'formguard.checks.FieldTrapCheck',
    'formguard.checks.TokenCheck',
    'formguard.checks.JsChallengeCheck',
]
```

## Further Reading

- [Custom Checks](docs/custom-checks.md) - write your own checks (CAPTCHA, rate limiting, etc.)
- [Advanced Usage](docs/advanced-usage.md) - per-form checks, decorator options
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
