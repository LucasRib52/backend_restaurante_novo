from django.urls import path
from .views import SubscriptionListCreateView, SubscriptionRetrieveUpdateView, CurrentSubscriptionView, PlanListCreateView, debug_subscriptions, create_test_subscription

urlpatterns = [
    path('', SubscriptionListCreateView.as_view(), name='subscription-list-create'),
    path('current/', CurrentSubscriptionView.as_view(), name='subscription-current'),
    path('plans/', PlanListCreateView.as_view(), name='plan-list-create'),
    path('<int:pk>/', SubscriptionRetrieveUpdateView.as_view(), name='subscription-detail-update'),
    path('debug/', debug_subscriptions, name='subscription-debug'),
    path('create-test/', create_test_subscription, name='subscription-create-test'),
] 