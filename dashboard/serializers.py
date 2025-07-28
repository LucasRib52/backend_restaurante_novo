from rest_framework import serializers
from .models import DailyStats, ProductStats, CategoryStats

class DailyStatsSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo DailyStats.
    Usado para exibir estatísticas diárias no dashboard.
    """
    class Meta:
        model = DailyStats
        fields = ('id', 'date', 'total_orders',
                 'total_revenue', 'average_order_value',
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class ProductStatsSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo ProductStats.
    Usado para exibir estatísticas de produtos no dashboard.
    """
    class Meta:
        model = ProductStats
        fields = ('id', 'product_name', 'total_quantity',
                 'total_revenue', 'period_start', 'period_end',
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class CategoryStatsSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo CategoryStats.
    Usado para exibir estatísticas de categorias no dashboard.
    """
    class Meta:
        model = CategoryStats
        fields = ('id', 'category_name', 'total_orders',
                 'total_revenue', 'period_start', 'period_end',
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class DashboardSummarySerializer(serializers.Serializer):
    """
    Serializer para resumo do dashboard.
    Combina várias estatísticas em uma única resposta.
    """
    today_orders = serializers.IntegerField()
    today_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    week_orders = serializers.IntegerField()
    week_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    month_orders = serializers.IntegerField()
    month_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    top_products = ProductStatsSerializer(many=True)
    top_categories = CategoryStatsSerializer(many=True)
    recent_orders = serializers.ListField(child=serializers.DictField()) 