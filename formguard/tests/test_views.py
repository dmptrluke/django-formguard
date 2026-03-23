import logging
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.core import signing
from django.test import TestCase

from formguard.signals import guard_failed
from formguard.test import GuardedFormTestMixin


class GuardedFormViewTests(GuardedFormTestMixin, TestCase):
    """Default view behavior: guard failures re-render the form with errors."""

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
        assert response.status_code == 200
        assert len(self.signal_received) == 1

    # fast submission re-renders form with errors
    def test_fast_submission_rerenders(self):
        now = 1000.0
        token = signing.dumps(now, salt='formguard')
        data = {'name': 'Bot', **self.guard_data(fg_token=token)}
        with patch('formguard.checks.time.time', return_value=now + 1):
            response = self.client.post('/test-form/', data)
        assert response.status_code == 200
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
        response = self.client.post('/test-form/', data)
        assert response.status_code == 302


class RejectSilentlyViewTests(GuardedFormTestMixin, TestCase):
    """Tests for guard_on_failure=reject_silently(): bots get fake success."""

    def setUp(self):
        self.signal_received = []

        def handler(sender, **kwargs):
            self.signal_received.append(kwargs)

        guard_failed.connect(handler)
        self.addCleanup(guard_failed.disconnect, handler)

    # clean submission passes through normally
    def test_clean_submission(self):
        data = {'name': 'Alice', **self.guard_data()}
        response = self.client.post('/test-reject/', data)
        assert response.status_code == 302
        assert response.url == '/success/'
        assert len(self.signal_received) == 0

    # guard failure redirects to success URL (no message)
    def test_guard_failure_redirects(self):
        data = {'name': 'Bot', **self.guard_data(website='http://spam.com')}
        response = self.client.post('/test-reject/', data)
        assert response.status_code == 302
        assert len(self.signal_received) == 1

    # guard failure with message adds Django success message
    def test_guard_failure_with_message(self):
        data = {'name': 'Bot', **self.guard_data(website='http://spam.com')}
        response = self.client.post('/test-reject-msg/', data)
        msgs = list(get_messages(response.wsgi_request))
        assert any('Thanks!' in str(m) for m in msgs)

    # no message when reject_silently has no message
    def test_no_message_without_config(self):
        data = {'name': 'Bot', **self.guard_data(website='http://spam.com')}
        response = self.client.post('/test-reject/', data)
        msgs = list(get_messages(response.wsgi_request))
        assert len(msgs) == 0

    # regular validation failure re-renders form, not silent redirect
    def test_validation_failure_rerenders(self):
        data = {**self.guard_data()}  # missing 'name'
        response = self.client.post('/test-reject/', data)
        assert response.status_code == 200


class CustomFailureHandlingTests(GuardedFormTestMixin, TestCase):
    """Tests for custom guard_on_failure callables."""

    # custom callable receives correct args
    def test_custom_callable_receives_args(self):
        data = {'name': 'Bot', **self.guard_data(website='http://spam.com')}
        response = self.client.post('/test-custom/', data)
        assert response.status_code == 200
        assert b'custom:/success/:' in response.content

    # custom callable is NOT invoked for regular validation failures
    def test_custom_callable_not_invoked_for_validation(self):
        data = {**self.guard_data()}  # missing 'name'
        response = self.client.post('/test-custom/', data)
        assert response.status_code == 200
        assert b'custom:' not in response.content

    # non-callable guard_on_failure raises ImproperlyConfigured
    def test_non_callable_raises(self):
        from django.core.exceptions import ImproperlyConfigured
        from django.test import RequestFactory

        from formguard.tests.views import TestForm, TestGuardedView

        factory = RequestFactory()
        request = factory.post('/test-form/', {'name': 'Bot', 'website': 'spam'})

        view = TestGuardedView()
        view.request = request
        view.guard_on_failure = 'not-callable'

        form = TestForm(data={'name': 'Bot', 'website': 'spam'}, request=request)
        form.is_valid()

        with self.assertRaises(ImproperlyConfigured):
            view.form_invalid(form)
