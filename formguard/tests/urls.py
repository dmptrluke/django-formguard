from django.urls import path

from formguard.tests.views import TestGuardedView, TestSilentMessageView, TestSilentView

urlpatterns = [
    path('test-form/', TestGuardedView.as_view(), name='test-form'),
    path('test-silent/', TestSilentView.as_view(), name='test-silent'),
    path('test-silent-msg/', TestSilentMessageView.as_view(), name='test-silent-msg'),
]
