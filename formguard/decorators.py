import functools

from django.http import HttpResponseRedirect

from formguard.checks import run_checks
from formguard.utils import add_success_message, handle_bot


def guard_form(form_class, success_url, auto_reject=True):
    """Decorator that validates guard checks on POST before calling the view.

    With auto_reject=True (default), bot submissions get a fake success redirect.
    With auto_reject=False, reasons are attached to request.formguard_reasons
    and the view is called normally.
    The bound form is passed as a 'form' keyword argument on POST.
    """

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method != 'POST':
                return view_func(request, *args, **kwargs)

            form = form_class(request.POST, request.FILES)
            if form.is_valid():
                reasons = run_checks(request, form)
                if reasons:
                    handle_bot(view_func, request, form, reasons)
                    if auto_reject:
                        add_success_message(request)
                        return HttpResponseRedirect(success_url)
                    else:
                        request.formguard_reasons = reasons

            return view_func(request, *args, form=form, **kwargs)

        return wrapper

    return decorator
