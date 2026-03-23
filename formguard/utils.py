import logging

logger = logging.getLogger('formguard')


def handle_bot(sender, request, form, reasons):
    """Log the guard check failure."""
    addr = request.META.get('REMOTE_ADDR', 'unknown')
    logger.warning('formguard triggered from %s: %s', addr, ', '.join(str(r) for r in reasons))
