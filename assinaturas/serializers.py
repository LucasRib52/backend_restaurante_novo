from rest_framework import serializers
from .models import Subscription, Plan
import logging

logger = logging.getLogger(__name__)

class SubscriptionSerializer(serializers.ModelSerializer):
    days_remaining = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = ['days_remaining', 'company']

    def get_days_remaining(self, obj):
        if obj.end_date:
            from datetime import date
            remaining = (obj.end_date - date.today()).days if obj.active else 0
            return remaining if remaining >= 0 else 0
        return None

    def to_representation(self, instance):
        """
        Sobrescreve para adicionar logs
        """
        logger.info(f"Serializando assinatura: ID={instance.id}, Plano={instance.plan}, Ativa={instance.active}")
        data = super().to_representation(instance)
        logger.info(f"Dados serializados: {data}")
        return data


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__' 