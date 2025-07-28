from django.urls import path
from .views import SettingsDetailView

urlpatterns = [
    path('me/', SettingsDetailView.as_view(), name='settings-detail'),
] 