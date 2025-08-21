from django.shortcuts import render
from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import Order, OrderItem, OrderItemIngredient
from .serializers import (
    OrderSerializer, OrderCreateSerializer,
    OrderUpdateSerializer, OrderItemSerializer
)
from settings.models import Settings
from rest_framework.pagination import PageNumberPagination


class OrdersPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """
        Retorna resposta paginada com contagem total correta.
        """
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

class CreateOrderView(views.APIView):
    """
    View para criar pedidos.
    """
    def post(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Pegar as configurações do sistema
            settings = request.user.settings  # utiliza settings do usuário
            if not settings:
                return Response(
                    {'error': 'Nenhuma configuração encontrada'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            order = serializer.save()
            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de pedidos.
    """
    serializer_class = OrderSerializer
    http_method_names = ['get', 'put', 'patch', 'delete', 'post']
    pagination_class = OrdersPagination

    def get_serializer_class(self):
        """
        Retorna o serializer apropriado baseado na ação.
        """
        if self.action == 'create':
            return OrderCreateSerializer
        if self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        return OrderSerializer

    def get_queryset(self):
        """
        Queryset otimizado com filtros e prefetch para evitar N+1.
        Suporta filtros via query params: status, last24h, restaurant_id.
        """
        qs = (
            Order.objects.select_related('restaurant', 'client_order')
            .prefetch_related(
                'items__product',
                'items__promotion',
                'items__ingredients',
                'items__ingredients__ingredient',
            )
            .order_by('-created_at')
        )

        # Filtrar por restaurante se fornecido
        restaurant_id = self.request.query_params.get('restaurant_id')
        if restaurant_id:
            qs = qs.filter(restaurant_id=restaurant_id)

        # Filtrar por status
        status_param = self.request.query_params.get('status')
        if status_param and status_param != 'all':
            qs = qs.filter(status=status_param)

        # Últimas 24 horas
        last24h = self.request.query_params.get('last24h')
        if last24h in ['1', 'true', 'True', 'yes', 'sim']:
            recent_time = timezone.now() - timedelta(hours=24)
            qs = qs.filter(created_at__gte=recent_time)

        return qs

    def create(self, request, *args, **kwargs):
        """
        Cria um novo pedido.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Pegar as configurações do sistema
            settings = request.user.settings
            if not settings:
                return Response(
                    {'error': 'Nenhuma configuração encontrada'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            order = serializer.save()
            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Atualiza o status de um pedido.
        """
        try:
            # Para update_status, usar queryset sem filtros de restaurante
            # para permitir acesso ao pedido específico
            order = Order.objects.get(pk=pk)
            
            # Verificar se o usuário tem acesso ao pedido
            if hasattr(request.user, 'settings') and request.user.settings:
                if order.restaurant != request.user.settings:
                    return Response(
                        {'error': 'Acesso negado a este pedido'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            new_status = request.data.get('status')
            
            if not new_status:
                return Response(
                    {'error': 'Status não fornecido'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if new_status not in dict(Order.STATUS_CHOICES):
                return Response(
                    {'error': f'Status inválido: {new_status}. Status válidos: {list(dict(Order.STATUS_CHOICES).keys())}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            order.status = new_status
            order.save()

            serializer = self.get_serializer(order)
            return Response(serializer.data)
            
        except Order.DoesNotExist:
            return Response(
                {'error': 'Pedido não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Erro ao atualizar status: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Retorna pedidos pendentes.
        """
        orders = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def preparing(self, request):
        """
        Retorna pedidos em preparo.
        """
        orders = self.get_queryset().filter(status='preparing')
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def ready(self, request):
        """
        Retorna pedidos prontos.
        """
        orders = self.get_queryset().filter(status='ready')
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        Retorna pedidos do dia atual.
        """
        today = timezone.now().date()
        orders = self.get_queryset().filter(
            created_at__date=today
        ).order_by('-created_at')
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Retorna pedidos recentes (últimas 24 horas).
        """
        recent_time = timezone.now() - timedelta(days=1)
        orders = self.get_queryset().filter(
            created_at__gte=recent_time
        ).order_by('-created_at')
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

class OrderItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de itens de pedido.
    """
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_queryset(self):
        """
        Retorna todos os itens de pedido.
        """
        return OrderItem.objects.all()

    def perform_create(self, serializer):
        """
        Cria um novo item de pedido.
        """
        order_id = self.request.data.get('order')
        try:
            order = Order.objects.get(id=order_id)
            serializer.save(order=order)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Pedido não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

class ListOrdersView(views.APIView):
    """
    View para listar pedidos.
    """
    def get(self, request, *args, **kwargs):
        orders = Order.objects.all().order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class PrinterSettingsView(views.APIView):
    """
    View para gerenciar configurações da impressora.
    """
    def get(self, request):
        settings = Settings.objects.first()
        return Response({
            'printer_name': settings.printer_name if settings else None
        })

    def post(self, request):
        settings, _ = Settings.objects.get_or_create()
        settings.printer_name = request.data.get('printer_name')
        settings.save()
        return Response({'status': 'success'})
