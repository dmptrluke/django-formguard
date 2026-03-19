from django import forms
from django.http import HttpResponse
from django.views.generic import FormView

from formguard.decorators import guard_form
from formguard.forms import GuardedFormMixin
from formguard.views import GuardedFormViewMixin


class TestForm(GuardedFormMixin, forms.Form):
    name = forms.CharField()


class TestGuardedView(GuardedFormViewMixin, FormView):
    form_class = TestForm
    template_name = 'formguard/tests/form.html'
    success_url = '/success/'

    def form_valid(self, form):
        if self.is_bot(form):
            return self.bot_response()
        return super().form_valid(form)


class DecoratorTestForm(GuardedFormMixin, forms.Form):
    name = forms.CharField()


@guard_form(form_class=DecoratorTestForm, success_url='/success/')
def test_fbv(request, form=None):
    return HttpResponse('OK')


@guard_form(form_class=DecoratorTestForm, success_url='/success/', auto_reject=False)
def test_fbv_annotate(request, form=None):
    if getattr(request, 'formguard_reasons', None):
        return HttpResponse('SPAM')
    return HttpResponse('OK')
