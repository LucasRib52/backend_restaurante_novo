from django.urls import path
from .views import OrderViewSet, OrderItemViewSet, CreateOrderView, ListOrdersView, PrinterSettingsView

urlpatterns = [
    path('', OrderViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='order-list'),
    path('<int:pk>/', OrderViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='order-detail'),
    path('<int:pk>/update-status/', OrderViewSet.as_view({'post': 'update_status'}), name='order-update-status'),
    path('printer-settings/', PrinterSettingsView.as_view(), name='printer-settings'),
] 