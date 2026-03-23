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


class TestSilentView(GuardedFormViewMixin, FormView):
    form_class = TestForm
    template_name = 'formguard/tests/form.html'
    success_url = '/success/'
    guard_silent_reject = True

    def form_valid(self, form):
        return super().form_valid(form)


class TestSilentMessageView(GuardedFormViewMixin, FormView):
    form_class = TestForm
    template_name = 'formguard/tests/form.html'
    success_url = '/success/'
    guard_silent_reject = True
    guard_silent_message = 'Thanks!'

    def form_valid(self, form):
        return super().form_valid(form)
