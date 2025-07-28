from django.urls import path
from .views import CreateClientOrderView

urlpatterns = [
    path('create/', CreateClientOrderView.as_view(), name='client-order-create'),
] 