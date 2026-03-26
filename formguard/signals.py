from django.dispatch import Signal

__all__ = ['guard_checked', 'guard_failed']

guard_failed = Signal()
guard_checked = Signal()
