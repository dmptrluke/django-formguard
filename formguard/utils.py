import logging

from formguard.conf import get_setting
from formguard.signals import guard_triggered

logger = logging.getLogger('formguard')


def handle_bot(sender, request, form, reasons):
    """Log, emit signal, and optionally add a success message."""
    addr = request.META.get('REMOTE_ADDR', 'unknown')
    logger.warning('formguard triggered from %s: %s', addr, ', '.join(reasons))
    guard_triggered.send(sender=sender, request=request, form=form, reasons=reasons)
    message = get_setting('SUCCESS_MESSAGE')
    if message:
        from django.contrib import messages

        messages.success(request, message)
