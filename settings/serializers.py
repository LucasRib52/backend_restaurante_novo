from rest_framework import serializers
from .models import Settings, OpeningHour
from datetime import datetime, time
from django.conf import settings as django_settings

class OpeningHourSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpeningHour
        fields = ['id', 'day_of_week', 'opening_time', 'closing_time', 'is_open', 'is_holiday', 'next_day_closing']

    def validate(self, data):
        opening_time = data.get('opening_time')
        closing_time = data.get('closing_time')
        
        if opening_time and closing_time:
            # Se o fechamento for menor que a abertura, automaticamente marca como fechamento no dia seguinte
            if closing_time < opening_time:
                data['next_day_closing'] = True
            else:
                data['next_day_closing'] = False
                
        return data

class SettingsSerializer(serializers.ModelSerializer):
    """
    Serializer para o model Settings.
    """
    opening_hours = OpeningHourSerializer(many=True, read_only=True)
    business_photo = serializers.ImageField(required=False, allow_null=True)
    business_slug = serializers.SlugField(required=False, allow_null=True)
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Settings
        fields = '__all__'
        extra_kwargs = {
            'business_name': {'required': False},
            'business_phone': {'required': False},
            'business_address': {'required': False},
            'business_email': {'required': False},
            'business_photo': {'required': False},
            'opening_time': {'required': False},
            'closing_time': {'required': False},
            'delivery_fee': {'required': False},
            'minimum_order_value': {'required': False},
            'tax_rate': {'required': False},
        }
    
    def get_logo_url(self, obj):
        if obj.business_photo:
            return f"{django_settings.MEDIA_URL}{obj.business_photo}"
        return None 