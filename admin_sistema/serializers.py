from rest_framework import serializers
from settings.models import Settings
from django.utils import timezone
from assinaturas.serializers import PlanSerializer

class CompanySerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_is_admin = serializers.BooleanField(source='owner.is_superuser', read_only=True)
    subscription_id = serializers.SerializerMethodField()
    plan = serializers.SerializerMethodField()
    start_date = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Settings
        fields = ['id', 'owner_username', 'owner_is_admin', 'business_name', 'business_email', 'business_phone', 'is_active', 'subscription_id', 'plan', 'start_date', 'end_date', 'days_remaining']

    def get_current_subscription(self, obj):
        return obj.subscriptions.filter(active=True).order_by('-start_date').first()

    def get_subscription_id(self, obj):
        sub = self.get_current_subscription(obj)
        return sub.id if sub else None

    def get_plan(self, obj):
        sub = self.get_current_subscription(obj)
        return sub.plan if sub else 'free'

    def get_start_date(self, obj):
        sub = self.get_current_subscription(obj)
        return sub.start_date if sub and sub.start_date else None

    def get_end_date(self, obj):
        sub = self.get_current_subscription(obj)
        return sub.end_date if sub and sub.end_date else None

    def get_days_remaining(self, obj):
        sub = self.get_current_subscription(obj)
        if sub and sub.end_date:
            remaining = (sub.end_date - timezone.now().date()).days
            return remaining if remaining >= 0 else 0
        return None 