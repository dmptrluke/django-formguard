from django import forms


class TurnstileWidget(forms.Widget):
    """Renders the Cloudflare Turnstile container div. The Turnstile script injects its own hidden input inside it."""

    template_name = 'formguard/contrib/turnstile/widget.html'

    def __init__(self, site_key, theme='auto', size='normal', attrs=None):
        super().__init__(attrs=attrs)
        self.site_key = site_key
        self.theme = theme
        self.size = size

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['site_key'] = self.site_key
        context['widget']['theme'] = self.theme
        context['widget']['size'] = self.size
        return context

    def value_from_datadict(self, data, files, name):
        return data.get('cf-turnstile-response', '')
