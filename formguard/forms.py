import time

from django.core import signing
from django.core.exceptions import ImproperlyConfigured
from django.forms import CharField, HiddenInput

from formguard.conf import JS_FIELD_NAME, SIGNING_SALT, TOKEN_FIELD_NAME, get_setting
from formguard.widgets import HoneypotWidget


class GuardedFormMixin:
    """Add a hidden honeypot field and a signed timestamp token to a form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        field_name = get_setting('FIELD_NAME')

        if field_name in self.fields:
            raise ImproperlyConfigured(
                f"Form already has a field named '{field_name}'. Set FORMGUARD_FIELD_NAME to a different value."
            )

        self.fields[field_name] = CharField(
            required=False,
            widget=HoneypotWidget(label=field_name.title()),
        )
        self.fields[TOKEN_FIELD_NAME] = CharField(
            required=False,
            widget=HiddenInput(attrs={'data-fg-token': True}),
            initial=self._make_token,
        )
        self.fields[JS_FIELD_NAME] = CharField(
            required=False,
            widget=HiddenInput(attrs={'data-fg-js': True}),
            initial='',
        )

    @staticmethod
    def _make_token():
        return signing.dumps(time.time(), salt=SIGNING_SALT)
