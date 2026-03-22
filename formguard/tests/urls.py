from django.urls import path

from formguard.tests.views import TestGuardedView, TestStealthMessageView, TestStealthView

urlpatterns = [
    path('test-form/', TestGuardedView.as_view(), name='test-form'),
    path('test-stealth/', TestStealthView.as_view(), name='test-stealth'),
    path('test-stealth-msg/', TestStealthMessageView.as_view(), name='test-stealth-msg'),
]
