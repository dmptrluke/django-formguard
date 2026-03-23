from django.apps import AppConfig
from django.core.checks import register


class FormGuardConfig(AppConfig):
    name = 'formguard'
    verbose_name = 'Django FormGuard'

    def ready(self):
        from formguard.systemchecks import check_settings

        register('formguard')(check_settings)
