from django.test import SimpleTestCase

from formguard.widgets import HoneypotWidget


class HoneypotWidgetTests(SimpleTestCase):
    # widget renders with the hiding wrapper div
    def test_renders_hiding_div(self):
        widget = HoneypotWidget()
        html = widget.render('website', '', attrs={'id': 'id_website'})
        assert 'fg-field' in html
        assert 'aria-hidden="true"' in html

    # widget sets tabindex and autocomplete attrs
    def test_accessibility_attrs(self):
        widget = HoneypotWidget()
        html = widget.render('website', '', attrs={'id': 'id_website'})
        assert 'tabindex="-1"' in html
        assert 'autocomplete="one-time-code"' in html

    # widget renders the label
    def test_renders_label(self):
        widget = HoneypotWidget(label='Website')
        html = widget.render('website', '', attrs={'id': 'id_website'})
        assert '<label' in html
        assert 'Website' in html

    # widget declares CSS in Media
    def test_media_declaration(self):
        widget = HoneypotWidget()
        assert 'formguard/formguard.css' in str(widget.media)

    # widget uses custom template
    def test_template_name(self):
        widget = HoneypotWidget()
        assert widget.template_name == 'formguard/widget.html'
