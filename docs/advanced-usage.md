# Configuration

## Per-Form Checks

By default, all forms use the global `FORMGUARD_CHECKS` setting. To use
different checks on a specific form, set `formguard_checks` on the class:

```python
class ContactForm(GuardedFormMixin, forms.Form):
    formguard_checks = [
        'formguard.checks.FieldTrapCheck',
        'formguard.checks.TokenCheck',
    ]
    name = forms.CharField()
    message = forms.CharField(widget=forms.Textarea)
```

When testing forms with per-form checks, pass the form class to
`guard_data()` so the helper generates data for the right checks:

```python
data = self.guard_data(form_class=ContactForm)
```

## Decorator Options

The `@guard_form` decorator auto-redirects bots by default. Set
`auto_reject=False` to annotate the request instead, so you can handle
bot detection yourself:

```python
@guard_form(form_class=ContactForm, success_url='/thanks/', auto_reject=False)
def contact_view(request, form=None):
    if getattr(request, 'formguard_reasons', None):
        # bot detected, but you decide what to do
        return render(request, 'thanks.html')
    send_email(form.cleaned_data)
    return redirect('/thanks/')
```

The decorator passes the bound form as a `form` keyword argument.
