import logging

from formguard.conf import get_setting
from formguard.signals import guard_triggered

logger = logging.getLogger('formguard')


def handle_bot(sender, request, form, reasons):
    """Log the detection and emit the guard_triggered signal."""
    addr = request.META.get('REMOTE_ADDR', 'unknown')
    logger.warning('formguard triggered from %s: %s', addr, ', '.join(reasons))
    guard_triggered.send(sender=sender, request=request, form=form, reasons=reasons)


def add_success_message(request):
    """Add the configured success message to the request, if set."""
    message = get_setting('SUCCESS_MESSAGE')
    if message:
        from django.contrib import messages

        messages.success(request, message)
