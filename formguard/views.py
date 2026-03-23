import types

from django.core.exceptions import ImproperlyConfigured


class GuardedFormViewMixin:
    """Pass request to guarded forms and handle guard failures."""

    guard_on_failure = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Wrap plain functions in staticmethod so descriptor protocol
        # doesn't bind self as the first argument when calling the handler.
        handler = cls.__dict__.get('guard_on_failure')
        if isinstance(handler, types.FunctionType):
            cls.guard_on_failure = staticmethod(handler)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_invalid(self, form):
        if form.guard_failures and self.guard_on_failure is not None:
            if not callable(self.guard_on_failure):
                raise ImproperlyConfigured(f'{self.__class__.__name__}.guard_on_failure must be callable.')
            return self.guard_on_failure(
                self.request,
                form,
                success_url=self.get_success_url(),
            )
        return super().form_invalid(form)
