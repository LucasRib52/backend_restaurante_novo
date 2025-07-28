from django.urls import path
from .views import CompanyListView, CompanyRetrieveUpdateView, DashboardMetricsView, PlanListCreateView, PlanRetrieveUpdateDestroyView

urlpatterns = [
    path('empresas/', CompanyListView.as_view(), name='company-list'),
    path('empresas/<int:pk>/', CompanyRetrieveUpdateView.as_view(), name='company-detail'),
    path('dashboard/', DashboardMetricsView.as_view(), name='dashboard-metrics'),
    path('plans/', PlanListCreateView.as_view(), name='plan-list'),
    path('plans/<int:pk>/', PlanRetrieveUpdateDestroyView.as_view(), name='plan-detail'),
] 