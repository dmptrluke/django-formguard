import time

from django import forms
from django.core import signing
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from formguard.forms import GuardedFormMixin
from formguard.widgets import HoneypotWidget


class SampleForm(GuardedFormMixin, forms.Form):
    name = forms.CharField()
    email = forms.EmailField()


class GuardedFormMixinTests(SimpleTestCase):
    # mixin adds honeypot field with HoneypotWidget
    def test_adds_honeypot_field(self):
        form = SampleForm()
        assert 'website' in form.fields
        assert isinstance(form.fields['website'].widget, HoneypotWidget)
        assert form.fields['website'].required is False

    # mixin adds token field as hidden input
    def test_adds_token_field(self):
        form = SampleForm()
        assert 'fg_token' in form.fields
        assert form.fields['fg_token'].required is False

    # token initial value is a valid signed timestamp
    def test_token_is_signed_timestamp(self):
        form = SampleForm()
        token = form.fields['fg_token'].initial
        if callable(token):
            token = token()
        loaded = signing.loads(token, salt='formguard')
        assert isinstance(loaded, float)
        assert abs(loaded - time.time()) < 5

    # field name collision with existing field raises
    def test_field_collision_raises(self):
        class BadForm(GuardedFormMixin, forms.Form):
            website = forms.CharField()

        with self.assertRaises(ImproperlyConfigured):
            BadForm()

    # custom field name from settings is respected
    @override_settings(FORMGUARD_FIELD_NAME='phone')
    def test_custom_field_name(self):
        form = SampleForm()
        assert 'phone' in form.fields
        assert 'website' not in form.fields

    # honeypot label is derived from field name
    @override_settings(FORMGUARD_FIELD_NAME='phone_number')
    def test_label_derived_from_field_name(self):
        form = SampleForm()
        widget = form.fields['phone_number'].widget
        assert widget.label == 'Phone_Number'

    # token field has data-fg-token attribute for JS
    def test_token_has_data_attribute(self):
        form = SampleForm()
        token_field = form.fields['fg_token']
        html = token_field.widget.render('fg_token', '', attrs={'id': 'id_fg_token'})
        assert 'data-fg-token' in html

    # mixin adds JS challenge field
    def test_adds_js_field(self):
        form = SampleForm()
        assert 'fg_js' in form.fields
        html = form.fields['fg_js'].widget.render('fg_js', '', attrs={'id': 'id_fg_js'})
        assert 'data-fg-js' in html
