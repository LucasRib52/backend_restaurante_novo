from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'products', views.ProductViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('store-info/', views.get_store_info, name='store-info'),
    path('<slug:business_slug>/', views.get_store_by_slug, name='store-by-slug'),
] 