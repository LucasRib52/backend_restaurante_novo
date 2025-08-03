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
        Retorna todos os pedidos.
        """
        if not self.request.user.is_authenticated:
            return Order.objects.none()
        return Order.objects.filter(restaurant=self.request.user.settings).order_by('-created_at')

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

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Atualiza o status de um pedido.
        """
        order = self.get_object()
        new_status = request.data.get('status')

        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'Status inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = new_status
        order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data)

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
