from django.urls import path

from formguard.tests.views import TestGuardedView, test_fbv, test_fbv_annotate

urlpatterns = [
    path('test-form/', TestGuardedView.as_view(), name='test-form'),
    path('test-fbv/', test_fbv, name='test-fbv'),
    path('test-fbv-annotate/', test_fbv_annotate, name='test-fbv-annotate'),
]
