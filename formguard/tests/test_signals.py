from django.test import SimpleTestCase

from formguard.signals import guard_triggered


class GuardTriggeredSignalTests(SimpleTestCase):
    # signal exists and can be connected
    def test_signal_exists(self):
        received = []

        def handler(sender, **kwargs):
            received.append(kwargs)

        guard_triggered.connect(handler)
        try:
            guard_triggered.send(
                sender=self.__class__,
                request=None,
                form=None,
                reasons=['test reason'],
            )
            assert len(received) == 1
            assert received[0]['reasons'] == ['test reason']
        finally:
            guard_triggered.disconnect(handler)
