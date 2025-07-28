from django.contrib import admin
from .models import Subscription

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('company', 'plan', 'start_date', 'end_date', 'active')
    list_filter = ('plan', 'active')
    search_fields = ('company__business_name',)
