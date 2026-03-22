from django import forms
from django.views.generic import FormView

from formguard.forms import GuardedFormMixin
from formguard.views import GuardedFormViewMixin


class TestForm(GuardedFormMixin, forms.Form):
    name = forms.CharField()


class TestGuardedView(GuardedFormViewMixin, FormView):
    form_class = TestForm
    template_name = 'formguard/tests/form.html'
    success_url = '/success/'

    def form_valid(self, form):
        return super().form_valid(form)


class TestStealthView(GuardedFormViewMixin, FormView):
    form_class = TestForm
    template_name = 'formguard/tests/form.html'
    success_url = '/success/'
    stealth_reject = True

    def form_valid(self, form):
        return super().form_valid(form)


class TestStealthMessageView(GuardedFormViewMixin, FormView):
    form_class = TestForm
    template_name = 'formguard/tests/form.html'
    success_url = '/success/'
    stealth_reject = True
    stealth_message = 'Thanks!'

    def form_valid(self, form):
        return super().form_valid(form)
