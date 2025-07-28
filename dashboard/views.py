from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import DailyStats, ProductStats, CategoryStats
from .serializers import (
    DailyStatsSerializer, ProductStatsSerializer,
    CategoryStatsSerializer, DashboardSummarySerializer
)
from orders.models import Order, OrderItem
from products.models import Product, Category

class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para o dashboard com estatísticas e métricas.
    """

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Retorna um resumo das estatísticas do dashboard.
        """
        try:
            # Parâmetros de período personalizados
            custom_month = request.query_params.get('month')  # Formato esperado YYYY-MM
            restaurant = request.user.settings  # separa métricas por restaurante
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)

            # Se o usuário solicitar um mês específico no formato YYYY-MM
            from datetime import date
            if custom_month:
                try:
                    year, month = map(int, custom_month.split('-'))
                    first_day_custom = date(year, month, 1)
                    # calcular último dia do mês
                    if month == 12:
                        last_day_custom = date(year + 1, 1, 1) - timedelta(days=1)
                    else:
                        last_day_custom = date(year, month + 1, 1) - timedelta(days=1)
                    month_filter_start = first_day_custom
                    month_filter_end = last_day_custom
                except ValueError:
                    custom_month = None  # formato inválido, ignorar

            if not custom_month:
                month_filter_start = month_ago
                month_filter_end = today

            # Estatísticas do dia
            today_orders = Order.objects.filter(restaurant=restaurant, created_at__date=today)
            accepted_statuses = ['confirmed', 'preparing', 'ready', 'delivered']
            today_stats = {
                'orders': today_orders.count(),
                'revenue': float(Order.objects.filter(restaurant=restaurant, created_at__date=today, status__in=accepted_statuses).aggregate(
                    total=Sum('total_amount')
                )['total'] or 0)
            }

            # Estatísticas da semana
            week_orders = Order.objects.filter(restaurant=restaurant, created_at__date__gte=week_ago)
            week_stats = {
                'orders': week_orders.count(),
                'revenue': float(Order.objects.filter(restaurant=restaurant, created_at__date__gte=week_ago, status__in=accepted_statuses).aggregate(
                    total=Sum('total_amount')
                )['total'] or 0)
            }

            # Estatísticas do mês
            month_orders = Order.objects.filter(
                restaurant=restaurant,
                created_at__date__gte=month_filter_start,
                created_at__date__lte=month_filter_end
            )
            month_stats = {
                'orders': month_orders.count(),
                'revenue': float(Order.objects.filter(
                    restaurant=restaurant,
                    created_at__date__gte=month_filter_start,
                    created_at__date__lte=month_filter_end,
                    status__in=accepted_statuses).aggregate(
                    total=Sum('total_amount')
                )['total'] or 0)
            }

            # Paginação
            limit = int(request.query_params.get('limit', 10))
            page = int(request.query_params.get('page', 1))
            offset = (page - 1) * limit
            total_orders = Order.objects.filter(restaurant=restaurant).count()
            recent_orders = Order.objects.filter(restaurant=restaurant).order_by('-created_at')[offset:offset+limit]

            data = {
                'today_orders': today_stats['orders'],
                'today_revenue': today_stats['revenue'],
                'week_orders': week_stats['orders'],
                'week_revenue': week_stats['revenue'],
                'month_orders': month_stats['orders'],
                'month_revenue': month_stats['revenue'],
                'cancelled_orders': Order.objects.filter(restaurant=restaurant, status='cancelled').count(),
                'recent_orders': [
                    {
                        'id': order.id,
                        'customer_name': order.customer_name,
                        'total_amount': float(order.total_amount),
                        'status': order.get_status_display(),
                        'created_at': order.created_at
                    }
                    for order in recent_orders
                ],
                'total_orders': total_orders
            }

            return Response(data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def daily_stats(self, request):
        """
        Retorna estatísticas diárias.
        """
        try:
            days = int(request.query_params.get('days', 7))
            start_date = timezone.now().date() - timedelta(days=days)

            stats = DailyStats.objects.filter(
                date__gte=start_date
            ).order_by('date')

            serializer = DailyStatsSerializer(stats, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def product_stats(self, request):
        """
        Retorna estatísticas de produtos.
        """
        try:
            days = int(request.query_params.get('days', 30))
            start_date = timezone.now().date() - timedelta(days=days)

            stats = ProductStats.objects.filter(
                period_start__gte=start_date
            ).order_by('-total_quantity')

            serializer = ProductStatsSerializer(stats, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def category_stats(self, request):
        """
        Retorna estatísticas de categorias.
        """
        try:
            days = int(request.query_params.get('days', 30))
            start_date = timezone.now().date() - timedelta(days=days)

            stats = CategoryStats.objects.filter(
                period_start__gte=start_date
            ).order_by('-total_revenue')

            serializer = CategoryStatsSerializer(stats, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
