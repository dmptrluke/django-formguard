from django.shortcuts import redirect


class reject_silently:  # noqa: N801
    """Redirect to success URL, pretending the form was accepted."""

    def __init__(self, message=None):
        self.message = message

    def __repr__(self):
        if self.message:
            return f'reject_silently(message={self.message!r})'
        return 'reject_silently()'

    def __call__(self, request, form, success_url=None, **kwargs):
        if self.message:
            from django.contrib import messages

            messages.success(request, self.message)
        return redirect(success_url)
