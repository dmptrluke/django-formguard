from django import forms
from django.http import HttpResponse
from django.views.generic import FormView

from formguard.forms import GuardedFormMixin
from formguard.handlers import reject_silently
from formguard.views import GuardedFormViewMixin


class TestForm(GuardedFormMixin, forms.Form):
    name = forms.CharField()


class TestGuardedView(GuardedFormViewMixin, FormView):
    form_class = TestForm
    template_name = 'formguard/tests/form.html'
    success_url = '/success/'

    def form_valid(self, form):
        return super().form_valid(form)


class TestRejectSilentlyView(GuardedFormViewMixin, FormView):
    form_class = TestForm
    template_name = 'formguard/tests/form.html'
    success_url = '/success/'
    guard_on_failure = reject_silently()

    def form_valid(self, form):
        return super().form_valid(form)


class TestRejectSilentlyMessageView(GuardedFormViewMixin, FormView):
    form_class = TestForm
    template_name = 'formguard/tests/form.html'
    success_url = '/success/'
    guard_on_failure = reject_silently(message='Thanks!')

    def form_valid(self, form):
        return super().form_valid(form)


def _custom_handler(request, form, success_url=None, **kwargs):
    return HttpResponse(f'custom:{success_url}:{len(form.guard_failures)}', status=200)


class TestCustomCallableView(GuardedFormViewMixin, FormView):
    form_class = TestForm
    template_name = 'formguard/tests/form.html'
    success_url = '/success/'
    guard_on_failure = _custom_handler

    def form_valid(self, form):
        return super().form_valid(form)


def _declining_handler(request, form, success_url=None, **kwargs):
    form.declining_handler_called = True
    return None  # noqa: RET501


class TestDecliningHandlerView(GuardedFormViewMixin, FormView):
    form_class = TestForm
    template_name = 'formguard/tests/form.html'
    success_url = '/success/'
    guard_on_failure = _declining_handler
