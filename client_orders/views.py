from django.shortcuts import render, get_object_or_404
from rest_framework import views, permissions, status
from rest_framework.response import Response
from .models import ClientOrder
from .serializers import ClientOrderCreateSerializer
from settings.models import Settings

# Create your views here.

class CreateClientOrderView(views.APIView):
    """
    View para criar pedidos de clientes sem autenticação.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        slug = request.data.get('business_slug')
        restaurant = get_object_or_404(Settings, business_slug=slug)
        serializer = ClientOrderCreateSerializer(data=request.data, context={'restaurant': restaurant})
        if serializer.is_valid():
            client_order = serializer.save()
            return Response({
                'id': client_order.order.id,
                'status': 'success',
                'message': 'Pedido criado com sucesso'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
