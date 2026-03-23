# Testing

FormGuard ships test helpers to make testing guarded forms easy.

## GuardedFormTestMixin

Mix `GuardedFormTestMixin` into your test case. It provides `guard_data()`,
which returns a dict with valid guard fields for all active checks.

```python
from django.test import TestCase
from formguard.test import GuardedFormTestMixin


class TestContactView(GuardedFormTestMixin, TestCase):
    def test_submission_works(self):
        data = {
            'name': 'Test',
            'email': 'test@example.com',
            'message': 'Hello',
            **self.guard_data(),
        }
        response = self.client.post('/contact/', data)
        assert response.status_code == 302
```

`guard_data()` adapts automatically when you change `FORMGUARD_CHECKS`.

## Per-Form Checks

If your form defines `guard_checks`, pass the form class so the helper
generates data for the right checks:

```python
from formguard.conf import default_checks

class LoginForm(GuardedFormMixin, forms.Form):
    guard_checks = default_checks(exclude=['formguard.checks.InteractionCheck'])
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class TestLoginView(GuardedFormTestMixin, TestCase):
    def test_submission_works(self):
        data = {
            'username': 'alice',
            'password': 'secret',
            **self.guard_data(form_class=LoginForm),
        }
        response = self.client.post('/login/', data)
        assert response.status_code == 302
```

## Custom Check test_data()

When writing a custom check, implement `test_data()` to return valid POST
data for your check's fields. `guard_data()` aggregates `test_data()` from
all active checks automatically.

```python
class MyCheck(BaseCheck):
    def get_fields(self):
        return {'my_field': forms.CharField(required=False)}

    def test_data(self):
        return {'my_field': 'valid-value'}

    def check(self, form):
        if form.cleaned_data.get('my_field') != 'valid-value':
            return 'invalid'
        return False
```
