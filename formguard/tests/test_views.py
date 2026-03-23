import logging
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.core import signing
from django.test import TestCase

from formguard.signals import guard_failed
from formguard.test import GuardedFormTestMixin


class GuardedFormViewTests(GuardedFormTestMixin, TestCase):
    """Tests for the default view (guard_silent_reject=False) -- errors re-render the form."""

    def setUp(self):
        self.signal_received = []

        def handler(sender, **kwargs):
            self.signal_received.append(kwargs)

        guard_failed.connect(handler)
        self.addCleanup(guard_failed.disconnect, handler)

    # clean submission passes through and signal is NOT emitted
    def test_clean_submission(self):
        data = {'name': 'Alice', **self.guard_data()}
        response = self.client.post('/test-form/', data)
        assert response.status_code == 302
        assert response.url == '/success/'
        assert len(self.signal_received) == 0

    # honeypot field filled re-renders form with errors (not silent)
    def test_honeypot_rerenders_with_errors(self):
        data = {'name': 'Bot', **self.guard_data(website='http://spam.com')}
        response = self.client.post('/test-form/', data)
        assert response.status_code == 200  # re-rendered form
        assert len(self.signal_received) == 1

    # fast submission re-renders form with errors
    def test_fast_submission_rerenders(self):
        now = 1000.0
        token = signing.dumps(now, salt='formguard')
        data = {'name': 'Bot', **self.guard_data(fg_token=token)}
        with patch('formguard.checks.time.time', return_value=now + 1):
            response = self.client.post('/test-form/', data)
        assert response.status_code == 200  # re-rendered form
        assert len(self.signal_received) == 1

    # bot detection is logged with IP address
    def test_bot_logged(self):
        with self.assertLogs('formguard', level=logging.WARNING) as cm:
            data = {'name': 'Bot', **self.guard_data(website='http://spam.com')}
            self.client.post('/test-form/', data)
        assert any('formguard' in msg.lower() for msg in cm.output)

    # get_form_kwargs injects request into the form
    def test_get_form_kwargs_injects_request(self):
        data = {'name': 'Alice', **self.guard_data()}
        # if request wasn't injected, is_valid() would raise ImproperlyConfigured
        response = self.client.post('/test-form/', data)
        assert response.status_code == 302


class SilentRejectViewTests(GuardedFormTestMixin, TestCase):
    """Tests for guard_silent_reject=True -- bots get fake success."""

    def setUp(self):
        self.signal_received = []

        def handler(sender, **kwargs):
            self.signal_received.append(kwargs)

        guard_failed.connect(handler)
        self.addCleanup(guard_failed.disconnect, handler)

    # clean submission passes through normally
    def test_clean_submission(self):
        data = {'name': 'Alice', **self.guard_data()}
        response = self.client.post('/test-silent/', data)
        assert response.status_code == 302
        assert response.url == '/success/'
        assert len(self.signal_received) == 0

    # honeypot triggers fake success redirect
    def test_honeypot_triggers_fake_success(self):
        data = {'name': 'Bot', **self.guard_data(website='http://spam.com')}
        response = self.client.post('/test-silent/', data)
        assert response.status_code == 302
        assert len(self.signal_received) == 1

    # bad signature triggers fake success
    def test_bad_signature_triggers(self):
        data = {'name': 'Bot', **self.guard_data(fg_token='tampered')}
        response = self.client.post('/test-silent/', data)
        assert response.status_code == 302
        assert len(self.signal_received) == 1

    # guard_silent_message adds success message to the redirect
    def test_silent_message(self):
        data = {'name': 'Bot', **self.guard_data(website='http://spam.com')}
        response = self.client.post('/test-silent-msg/', data)
        msgs = list(get_messages(response.wsgi_request))
        assert any('Thanks!' in str(m) for m in msgs)

    # no message when guard_silent_message is not set
    def test_no_message_when_not_set(self):
        data = {'name': 'Bot', **self.guard_data(website='http://spam.com')}
        response = self.client.post('/test-silent/', data)
        msgs = list(get_messages(response.wsgi_request))
        assert len(msgs) == 0

    # invalid form (missing required field) without guard failure re-renders normally
    def test_invalid_form_no_silent_reject(self):
        data = {**self.guard_data()}  # missing 'name'
        response = self.client.post('/test-silent/', data)
        assert response.status_code == 200  # re-rendered, not silent redirect
