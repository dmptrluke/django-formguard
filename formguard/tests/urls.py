from django.urls import path

from formguard.tests.views import (
    TestCustomCallableView,
    TestGuardedView,
    TestRejectSilentlyMessageView,
    TestRejectSilentlyView,
)

urlpatterns = [
    path('test-form/', TestGuardedView.as_view(), name='test-form'),
    path('test-reject/', TestRejectSilentlyView.as_view(), name='test-reject'),
    path(
        'test-reject-msg/',
        TestRejectSilentlyMessageView.as_view(),
        name='test-reject-msg',
    ),
    path('test-custom/', TestCustomCallableView.as_view(), name='test-custom'),
]
