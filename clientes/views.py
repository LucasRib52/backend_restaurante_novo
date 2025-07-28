from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from settings.models import Settings
from products.models import Category, Product
from .serializers import SettingsSerializer, CategorySerializer, ProductSerializer

# Create your views here.

@api_view(['GET'])
@permission_classes([AllowAny])
def get_store_info(request):
    """Retorna as informações da loja"""
    try:
        settings = Settings.objects.first()
        if not settings:
            return Response({'error': 'Configurações não encontradas'}, status=404)
        
        serializer = SettingsSerializer(settings, context={'request': request})
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_store_by_slug(request, business_slug):
    """Retorna as informações da loja pelo slug"""
    try:
        settings = get_object_or_404(Settings, business_slug=business_slug)
        serializer = SettingsSerializer(settings, context={'request': request})
        return Response(serializer.data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

class NoPagination(PageNumberPagination):
    page_size = None

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para listar categorias"""
    permission_classes = [AllowAny]
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = Category.objects.filter(is_active=True)
        slug = self.request.query_params.get('business_slug')
        if slug:
            queryset = queryset.filter(restaurant__business_slug=slug)
        return queryset.order_by('name')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para listar produtos"""
    permission_classes = [AllowAny]
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    pagination_class = NoPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        slug = self.request.query_params.get('business_slug')
        if slug:
            queryset = queryset.filter(restaurant__business_slug=slug)
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset.order_by('created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
