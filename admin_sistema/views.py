from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from settings.models import Settings
from assinaturas.models import Subscription
from .serializers import CompanySerializer

# Create your views here.

class CompanyListView(generics.ListAPIView):
    queryset = Settings.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]

class CompanyRetrieveUpdateView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Settings.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        # delete the company settings and the associated user
        instance = self.get_object()
        owner = instance.owner
        self.perform_destroy(instance)
        # delete the user account
        owner.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class DashboardMetricsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Parâmetros de filtro
        period = request.query_params.get('period', 'all')  # all, month, year
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Filtros de data
        date_filter = Q()
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                date_filter = Q(created_at__range=[start, end])
            except ValueError:
                pass
        elif period == 'month':
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            date_filter = Q(created_at__gte=current_month)
        elif period == 'year':
            current_year = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            date_filter = Q(created_at__gte=current_year)
        
        # Métricas básicas
        total_companies = Settings.objects.filter(date_filter).count()
        active_companies = Settings.objects.filter(date_filter, is_active=True).count()
        blocked_companies = Settings.objects.filter(date_filter, is_active=False).count()
        total_subscriptions = Subscription.objects.filter(date_filter).count()
        active_subscriptions = Subscription.objects.filter(date_filter, active=True).count()
        
        # Cálculo de faturamento (simulado - ajuste conforme sua lógica de negócio)
        # Assumindo que cada assinatura ativa gera R$ 99,90 por mês
        monthly_revenue = active_subscriptions * 99.90
        yearly_revenue = monthly_revenue * 12
        
        # Faturamento do mês atual
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_subscriptions = Subscription.objects.filter(
            active=True, 
            created_at__gte=current_month
        ).count()
        current_month_revenue = current_month_subscriptions * 99.90
        
        # Faturamento do ano atual
        current_year = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        current_year_subscriptions = Subscription.objects.filter(
            active=True, 
            created_at__gte=current_year
        ).count()
        current_year_revenue = current_year_subscriptions * 99.90
        
        # Dados para gráficos de tendência
        last_7_days = []
        for i in range(7):
            date = timezone.now() - timedelta(days=i)
            day_companies = Settings.objects.filter(
                created_at__date=date.date()
            ).count()
            day_subscriptions = Subscription.objects.filter(
                created_at__date=date.date()
            ).count()
            last_7_days.append({
                'date': date.strftime('%Y-%m-%d'),
                'companies': day_companies,
                'subscriptions': day_subscriptions
            })
        last_7_days.reverse()
        
        return Response({
            'total_companies': total_companies,
            'active_companies': active_companies,
            'blocked_companies': blocked_companies,
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'monthly_revenue': round(monthly_revenue, 2),
            'yearly_revenue': round(yearly_revenue, 2),
            'current_month_revenue': round(current_month_revenue, 2),
            'current_year_revenue': round(current_year_revenue, 2),
            'trend_data': last_7_days,
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
        })
