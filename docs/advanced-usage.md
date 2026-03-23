# Advanced Usage

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

## Silent Reject

By default, guard check failures re-render the form with errors like any
other form validation. To silently redirect bots to a fake success page
instead, set `guard_silent_reject = True` on the view:

```python
class ContactView(GuardedFormViewMixin, FormView):
    form_class = ContactForm
    template_name = 'contact.html'
    success_url = '/thanks/'
    guard_silent_reject = True
    guard_silent_message = 'Your message has been sent.'  # optional
```

With `guard_silent_reject = True`, bots get a redirect to `success_url`. Set
`guard_silent_message` to add a Django success message to the redirect (making
it indistinguishable from a real submission). Regular validation errors
(e.g. missing required fields) still re-render the form normally.

## Function-Based Views

Pass `request` when constructing the form:

```python
def contact_view(request):
    form = ContactForm(request.POST or None, request=request)
    if request.method == 'POST' and form.is_valid():
        send_email(form.cleaned_data)
        return redirect('/thanks/')
    return render(request, 'contact.html', {'form': form})
```

Guard checks run automatically inside `is_valid()`. If any check triggers,
the form is invalid and `form.guard_failures` contains the reason strings.
