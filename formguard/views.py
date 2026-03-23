from django.http import HttpResponseRedirect


class GuardedFormViewMixin:
    """Pass request to guarded forms and optionally silent-reject bots."""

    guard_silent_reject = False
    guard_silent_message = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_invalid(self, form):
        if self.guard_silent_reject and form.guard_failures:
            if self.guard_silent_message:
                from django.contrib import messages

                messages.success(self.request, self.guard_silent_message)
            return HttpResponseRedirect(self.get_success_url())
        return super().form_invalid(form)
