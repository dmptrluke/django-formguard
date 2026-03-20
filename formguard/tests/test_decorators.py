from django.test import TestCase

from formguard.signals import guard_triggered
from formguard.test import GuardedFormTestMixin


class GuardFormDecoratorTests(GuardedFormTestMixin, TestCase):
    def setUp(self):
        self.signal_received = []

        def handler(sender, **kwargs):
            self.signal_received.append(kwargs)

        guard_triggered.connect(handler)
        self.addCleanup(guard_triggered.disconnect, handler)

    # GET requests pass through to the wrapped view
    def test_get_passes_through(self):
        response = self.client.get('/test-fbv/')
        assert response.status_code == 200
        assert response.content == b'OK'

    # clean POST passes through with form kwarg
    def test_clean_post_passes(self):
        data = {'name': 'Alice', **self.guard_data()}
        response = self.client.post('/test-fbv/', data)
        assert response.status_code == 200
        assert response.content == b'OK'

    # bot POST returns redirect and emits signal
    def test_bot_post_redirects(self):
        data = {'name': 'Bot', **self.guard_data(website='http://spam.com')}
        response = self.client.post('/test-fbv/', data)
        assert response.status_code == 302
        assert len(self.signal_received) == 1

    # invalid form passes through to the view with form kwarg
    def test_invalid_form_passes_through(self):
        data = {**self.guard_data()}
        response = self.client.post('/test-fbv/', data)
        assert response.status_code == 200


class GuardFormAnnotateModeTests(GuardedFormTestMixin, TestCase):
    # auto_reject=False annotates request instead of redirecting
    def test_annotate_mode_bot(self):
        data = {'name': 'Bot', **self.guard_data(website='http://spam.com')}
        response = self.client.post('/test-fbv-annotate/', data)
        assert response.status_code == 200
        assert response.content == b'SPAM'

    # annotate mode passes clean submissions normally
    def test_annotate_mode_clean(self):
        data = {'name': 'Alice', **self.guard_data()}
        response = self.client.post('/test-fbv-annotate/', data)
        assert response.status_code == 200
        assert response.content == b'OK'
