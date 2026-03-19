from django.http import HttpResponseRedirect

from formguard.checks import run_checks
from formguard.utils import add_success_message, handle_bot


class GuardedFormViewMixin:
    """Run guard checks on form submission. Call is_bot() in form_valid()."""

    def is_bot(self, form):
        """Run all configured checks. Return True if any triggered."""
        reasons = run_checks(self.request, form)
        if reasons:
            handle_bot(self.__class__, self.request, form, reasons)
            return True
        return False

    def bot_response(self):
        """Return a response indistinguishable from a real success."""
        add_success_message(self.request)
        return HttpResponseRedirect(self.get_success_url())
