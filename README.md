# django-formguard

Invisible, layered form protection for Django. Combines honeypot fields, signed
timestamps, and a pluggable check pipeline to block bots without
user friction. Bots receive a fake success response indistinguishable from a
real one.

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

FormGuard's CSS and JS are declared as widget media. Include `{{ form.media }}`
in your template's `<head>` so the honeypot field is hidden and the JS check
runs.

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

The decorator passes the bound form as a `form` keyword argument. Set
`auto_reject=False` to annotate the request instead of auto-redirecting:

```python
@guard_form(form_class=ContactForm, success_url='/thanks/', auto_reject=False)
def contact_view(request, form=None):
    if getattr(request, 'formguard_reasons', None):
        # bot detected, but you decide what to do
        return render(request, 'thanks.html')
    send_email(form.cleaned_data)
    return redirect('/thanks/')
```

## How It Works

FormGuard runs a pipeline of checks against each form submission:

1. **Field trap** - A hidden honeypot field that should always be empty. Bots
   that fill all visible fields get caught.
2. **Timing** - A signed timestamp records when the form was loaded. Submissions
   faster than `FORMGUARD_MIN_SECONDS` are flagged.
3. **Signature** - The timestamp token is cryptographically signed. Tampered or
   expired tokens are rejected.
4. **JS challenge** - A JavaScript snippet sets a hidden field value that bots
   without JS execution can't fake.

All checks are invisible to real users. The honeypot field is hidden via CSS,
and the timing/signature checks happen server-side.

## Settings

All settings are optional. Defaults work out of the box.

| Setting | Default | Description |
|---|---|---|
| `FORMGUARD_FIELD_NAME` | `'website'` | Honeypot field name (label is derived via `.title()`) |
| `FORMGUARD_MIN_SECONDS` | `3` | Minimum seconds before a submission is accepted |
| `FORMGUARD_MAX_SECONDS` | `3600` | Maximum token age before expiry |
| `FORMGUARD_SUCCESS_MESSAGE` | `None` | Fake success message shown to bots |
| `FORMGUARD_CHECKS` | `['formguard.checks.field_trap', 'formguard.checks.timing', 'formguard.checks.signature', 'formguard.checks.js_challenge']` | Ordered list of check callables |

## Custom Checks

Write a function that takes `(request, form)` and returns `False` if the
submission is clean, or a reason string if it should be blocked:

```python
# myapp/checks.py
def rate_limit(request, form):
    ip = request.META.get('REMOTE_ADDR')
    if is_rate_limited(ip):
        return 'rate limited'
    return False
```

Register it in settings:

```python
FORMGUARD_CHECKS = [
    'formguard.checks.field_trap',
    'formguard.checks.timing',
    'formguard.checks.signature',
    'formguard.checks.js_challenge',
    'myapp.checks.rate_limit',
]
```

If a custom check raises an exception, it is logged and skipped (fail-open).

## Signals

The `guard_triggered` signal is emitted whenever a submission is flagged:

```python
from formguard.signals import guard_triggered

def on_guard_triggered(sender, request, form, reasons, **kwargs):
    # log to monitoring, increment counter, etc.
    pass

guard_triggered.connect(on_guard_triggered)
```

## Testing

FormGuard ships test helpers to make testing guarded forms easy:

```python
from formguard.test import GuardedFormTestMixin, make_guard_token

class TestContactView(GuardedFormTestMixin, TestCase):
    def test_submission_works(self):
        data = {
            'name': 'Test',
            'email': 'test@example.com',
            'message': 'Hello',
            **self.guard_data(),  # adds valid token + empty honeypot
        }
        response = self.client.post('/contact/', data)
        assert response.status_code == 302
```

`make_guard_token()` creates a valid signed token for use in test POST data.
`GuardedFormTestMixin.guard_data()` returns a dict with all required guard
fields pre-filled.

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
