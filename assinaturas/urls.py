from django.urls import path
from .views import SubscriptionListCreateView, SubscriptionRetrieveUpdateView

urlpatterns = [
    path('', SubscriptionListCreateView.as_view(), name='subscription-list-create'),
    path('<int:pk>/', SubscriptionRetrieveUpdateView.as_view(), name='subscription-detail-update'),
] 