from django.forms.widgets import TextInput


class HoneypotWidget(TextInput):
    """Text input wrapped in a hiding container. Invisible to humans, attractive to bots."""

    template_name = 'formguard/widget.html'

    class Media:
        css = {'all': ('formguard/formguard.css',)}
        js = ('formguard/formguard.js',)

    def __init__(self, label='Website', attrs=None):
        self.label = label
        defaults = {
            'tabindex': '-1',
            'autocomplete': 'one-time-code',
        }
        if attrs:
            defaults.update(attrs)
        super().__init__(attrs=defaults)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['label'] = self.label
        return context
