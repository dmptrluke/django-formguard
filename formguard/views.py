from django.http import HttpResponseRedirect


class GuardedFormViewMixin:
    """Pass request to guarded forms and optionally stealth-reject bots."""

    stealth_reject = False
    stealth_message = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_invalid(self, form):
        if self.stealth_reject and form.guard_failures:
            if self.stealth_message:
                from django.contrib import messages

                messages.success(self.request, self.stealth_message)
            return HttpResponseRedirect(self.get_success_url())
        return super().form_invalid(form)
