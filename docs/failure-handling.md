# Failure Handling

By default, guard check failures produce form validation errors. To silently
redirect bots instead, set `guard_on_failure` on the view.

## `reject_silently`

Redirect bots to the success URL so they think the form was accepted:

```python
from formguard.handlers import reject_silently
from formguard.views import GuardedFormViewMixin

class ContactView(GuardedFormViewMixin, FormView):
    form_class = ContactForm
    template_name = 'contact.html'
    success_url = '/thanks/'
    guard_on_failure = reject_silently()
```

Add a Django success message to the redirect:

```python
guard_on_failure = reject_silently(message='Your message has been sent.')
```

Regular validation errors (e.g. missing required fields) still re-render the
form normally. Only guard check failures are silently rejected.

## Custom callable

Write any callable with the signature `(request, form, success_url=None, **kwargs)`:

```python
from django.shortcuts import redirect

def log_and_reject(request, form, success_url=None, **kwargs):
    analytics.track('bot_blocked', ip=request.META['REMOTE_ADDR'])
    return redirect(success_url)

class ContactView(GuardedFormViewMixin, FormView):
    form_class = ContactForm
    success_url = '/thanks/'
    guard_on_failure = log_and_reject
```

The callable must return an `HttpResponse`. `form.guard_failures` contains the
list of `GuardResult` objects that triggered the failure.

## Override `form_invalid()`

For full control with access to `self` (the view instance), override
Django's `form_invalid()` and check `form.guard_failures` directly:

```python
class ContactView(GuardedFormViewMixin, FormView):
    form_class = ContactForm
    success_url = '/thanks/'

    def form_invalid(self, form):
        if form.guard_failures:
            ban_ip(self.request.META['REMOTE_ADDR'])
            return redirect(self.get_success_url())
        return super().form_invalid(form)
```

For function-based views, see [Function-Based Views](function-based-views.md).
