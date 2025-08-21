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
            
            # Buscar configurações do restaurante (fallback se não autenticado)
            try:
                restaurant = request.user.settings if hasattr(request, 'user') and request.user.is_authenticated else None
            except:
                restaurant = None
                
            # Se não tem restaurante específico, usar todos os pedidos
            if not restaurant:
                from settings.models import Settings
                restaurant = Settings.objects.first()
            
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

            # Base queryset por restaurante
            accepted_statuses = ['confirmed', 'preparing', 'ready', 'delivered']
            base_qs = Order.objects.all()
            if restaurant:
                base_qs = base_qs.filter(restaurant=restaurant)

            # Determinar período solicitado
            period = request.query_params.get('period', 'today')
            start_param = request.query_params.get('start_date')  # YYYY-MM-DD
            end_param = request.query_params.get('end_date')      # YYYY-MM-DD

            # Datas padrão
            start_date = None
            end_date = None

            if period == 'today':
                start_date, end_date = today, today
            elif period == 'week':
                start_date, end_date = week_ago, today
            elif period == 'month':
                start_date, end_date = month_ago, today
            elif period == 'lastMonth':
                from datetime import date
                first_day_last = date(today.year, today.month - 1 if today.month > 1 else 12, 1)
                if today.month == 1:
                    last_day_last = date(today.year, 1, 1) - timedelta(days=1)
                else:
                    last_day_last = date(today.year, today.month, 1) - timedelta(days=1)
                start_date, end_date = first_day_last, last_day_last
            elif period == 'custom':
                if start_param and end_param:
                    try:
                        y1, m1, d1 = map(int, start_param.split('-'))
                        y2, m2, d2 = map(int, end_param.split('-'))
                        from datetime import date
                        start_date = date(y1, m1, d1)
                        end_date = date(y2, m2, d2)
                    except Exception:
                        start_date, end_date = month_ago, today
                elif custom_month:
                    start_date, end_date = month_filter_start, month_filter_end
                else:
                    start_date, end_date = month_ago, today
            elif period == 'all':
                start_date, end_date = None, None
            else:
                start_date, end_date = week_ago, today

            # Queryset do período
            period_qs = base_qs
            if start_date and end_date:
                period_qs = period_qs.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)

            # Estatísticas auxiliares (hoje/semana/mês) para cards laterais
            today_qs = base_qs.filter(created_at__date=today)
            week_qs = base_qs.filter(created_at__date__gte=week_ago)
            month_qs = base_qs.filter(created_at__date__gte=month_filter_start, created_at__date__lte=month_filter_end)

            today_stats = {
                'orders': today_qs.count(),
                'revenue': float(today_qs.filter(status__in=accepted_statuses).aggregate(total=Sum('total_amount'))['total'] or 0)
            }
            week_stats = {
                'orders': week_qs.count(),
                'revenue': float(week_qs.filter(status__in=accepted_statuses).aggregate(total=Sum('total_amount'))['total'] or 0)
            }
            month_stats = {
                'orders': month_qs.count(),
                'revenue': float(month_qs.filter(status__in=accepted_statuses).aggregate(total=Sum('total_amount'))['total'] or 0)
            }

            # Paginação para pedidos recentes do período
            limit = int(request.query_params.get('limit', 10))
            page = int(request.query_params.get('page', 1))
            offset = (page - 1) * limit
            recent_orders = period_qs.order_by('-created_at')[offset:offset+limit]

            # Totais
            total_orders = base_qs.count()
            total_revenue = float(base_qs.filter(status__in=accepted_statuses).aggregate(total=Sum('total_amount'))['total'] or 0)

            # Totais do período
            period_orders = period_qs.count()
            period_revenue = float(period_qs.filter(status__in=accepted_statuses).aggregate(total=Sum('total_amount'))['total'] or 0)
            period_pending = period_qs.filter(status='pending').count()
            period_cancelled = period_qs.filter(status='cancelled').count()
            period_completed = period_qs.filter(status__in=accepted_statuses).count()

            data = {
                'today_orders': today_stats['orders'],
                'today_revenue': today_stats['revenue'],
                'week_orders': week_stats['orders'],
                'week_revenue': week_stats['revenue'],
                'month_orders': month_stats['orders'],
                'month_revenue': month_stats['revenue'],
                'cancelled_orders': base_qs.filter(status='cancelled').count(),
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
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'period': period,
                'period_orders': period_orders,
                'period_revenue': period_revenue,
                'period_pending': period_pending,
                'period_completed': period_completed,
                'period_cancelled': period_cancelled,
                'period_start_date': str(start_date) if start_date else None,
                'period_end_date': str(end_date) if end_date else None,
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
