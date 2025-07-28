from django.contrib import admin
from .models import Subscription, Plan

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('company', 'plan', 'start_date', 'end_date', 'active')
    list_filter = ('plan', 'active')
    search_fields = ('company__business_name',)

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days')
