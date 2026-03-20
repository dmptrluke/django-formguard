import logging
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.core import signing
from django.test import TestCase, override_settings

from formguard.signals import guard_triggered
from formguard.test import GuardedFormTestMixin


class GuardedFormViewMixinTests(GuardedFormTestMixin, TestCase):
    def setUp(self):
        self.signal_received = []

        def handler(sender, **kwargs):
            self.signal_received.append(kwargs)

        guard_triggered.connect(handler)
        self.addCleanup(guard_triggered.disconnect, handler)

    # clean submission passes through and signal is NOT emitted
    def test_clean_submission(self):
        data = {'name': 'Alice', **self.guard_data()}
        response = self.client.post('/test-form/', data)
        assert response.status_code == 302
        assert response.url == '/success/'
        assert len(self.signal_received) == 0

    # honeypot field filled returns fake success and emits signal
    def test_honeypot_triggers_fake_success(self):
        data = {'name': 'Bot', **self.guard_data(website='http://spam.com')}
        response = self.client.post('/test-form/', data)
        assert response.status_code == 302
        assert len(self.signal_received) == 1

    # fast submission returns fake success
    def test_fast_submission_triggers(self):
        now = 1000.0
        token = signing.dumps(now, salt='formguard')
        data = {'name': 'Bot', **self.guard_data(fg_token=token)}
        with patch('formguard.checks.time.time', return_value=now + 1):
            response = self.client.post('/test-form/', data)
        assert response.status_code == 302
        assert len(self.signal_received) == 1

    # bad signature returns fake success
    def test_bad_signature_triggers(self):
        data = {'name': 'Bot', **self.guard_data(fg_token='tampered')}
        response = self.client.post('/test-form/', data)
        assert response.status_code == 302
        assert len(self.signal_received) == 1

    # bot_response includes success message when configured
    @override_settings(FORMGUARD_SUCCESS_MESSAGE='Thanks!')
    def test_bot_response_includes_message(self):
        data = {'name': 'Bot', **self.guard_data(website='http://spam.com')}
        response = self.client.post('/test-form/', data)
        messages = list(get_messages(response.wsgi_request))
        assert any('Thanks!' in str(m) for m in messages)

    # no message when SUCCESS_MESSAGE is None
    def test_no_message_when_none(self):
        data = {'name': 'Bot', **self.guard_data(website='http://spam.com')}
        response = self.client.post('/test-form/', data)
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 0

    # bot detection is logged with IP address
    def test_bot_logged(self):
        with self.assertLogs('formguard', level=logging.WARNING) as cm:
            data = {'name': 'Bot', **self.guard_data(website='http://spam.com')}
            self.client.post('/test-form/', data)
        assert any('formguard' in msg.lower() for msg in cm.output)
