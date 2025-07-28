"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenObtainPairView, verify_token, register

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # JWT Authentication
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/verify-token/', verify_token, name='verify_token'),
    path('api/register/', register, name='register'),
    
    # Apps
    path('api/products/', include('products.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/settings/', include('settings.urls')),
    path('api/clientes/', include('clientes.urls')),
    path('api/client-orders/', include('client_orders.urls')),
    path('api/assinaturas/', include('assinaturas.urls')),  # assinaturas admin
    path('api/admin/', include('admin_sistema.urls')),  # painel admin-sistema
]

# Servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
