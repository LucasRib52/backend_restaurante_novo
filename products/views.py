from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Sum, Count
from .models import Category, Product, Ingredient, ProductIngredient, IngredientCategory, Promotion, PromotionItem, PromotionReward
from .serializers import (
    CategorySerializer, ProductSerializer,
    ProductDetailSerializer, IngredientSerializer,
    ProductIngredientSerializer, PromotionSerializer,
    PromotionCreateSerializer
)
import json


# Create your views here.

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de categorias.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None  # ✅ desativa com segurança e clareza


    def get_queryset(self):
        return Category.objects.filter(restaurant=self.request.user.settings)

    def perform_create(self, serializer):
        serializer.save(restaurant=self.request.user.settings)

    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """
        Retorna todos os produtos de uma categoria específica.
        """
        category = self.get_object()
        products = Product.objects.filter(category=category)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de produtos.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = None  # ✅ desativa com segurança e clareza


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_serializer_class(self):
        """
        Retorna o serializer apropriado baseado na ação.
        """
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer

    def get_queryset(self):
        """
        Retorna a lista de produtos ordenada por data de criação crescente.
        """
        queryset = Product.objects.filter(restaurant=self.request.user.settings)
        category_id = self.request.query_params.get('category', None)
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    def perform_create(self, serializer):
        """
        Cria um novo produto e seus ingredientes.
        """
        print("Iniciando criação do produto...")
        # Primeiro, salva o produto vinculando à restaurante do usuário
        product = serializer.save(restaurant=self.request.user.settings)
        print(f"Produto criado: {product.name}")
        
        # Processa os ingredientes
        ingredients = []
        for key in self.request.data:
            if key.startswith('ingredients['):
                ingredients.append(self.request.data[key])
            
        print("Ingredientes recebidos:", ingredients)
        
        # Agrupa ingredientes por grupo para garantir consistência
        group_map = {}
        for ing_data in ingredients:
            try:
                # Tenta decodificar o JSON
                ing_obj = json.loads(ing_data)
                print("Processando ingrediente:", ing_obj)
                
                ing_name = ing_obj.get('name')
                group_name = ing_obj.get('groupName')  # Mudando de category para groupName
                is_required = ing_obj.get('isRequired', False)
                max_quantity = ing_obj.get('maxQuantity', 1)
                is_extra = bool(ing_obj.get('isExtra', False))
                price = ing_obj.get('price', 0)
                print(f"DEBUG: Ingrediente {ing_name} - preço recebido: {price} (tipo: {type(price)})")
                
                if not ing_name or not group_name:
                    print("Nome do ingrediente ou grupo vazio, pulando...")
                    continue
                
                print(f"Processando ingrediente: {ing_name} (grupo: {group_name}, extra: {is_extra}, preço: {price})")
                
                # Organiza por grupo
                if group_name not in group_map:
                    group_map[group_name] = {
                        'is_required': is_required,
                        'max_quantity': max_quantity,
                        'is_extra': is_extra,
                        'ingredients': []
                    }
                group_map[group_name]['ingredients'].append({
                    'name': ing_name,
                    'price': price
                })
                print(f"DEBUG: Adicionado ao grupo {group_name}: {ing_name} com preço {price}")
                
            except Exception as e:
                print(f"Erro ao processar ingrediente: {str(e)}")
                continue
        
        # Processa cada grupo
        for group_name, group_data in group_map.items():
            for ing_data in group_data['ingredients']:
                try:
                    # Cria ou obtém o ingrediente
                    ingredient, created = Ingredient.objects.get_or_create(
                        name=ing_data['name'],
                        defaults={
                            'category': None,
                            'price': ing_data['price'],
                            'is_extra': group_data['is_extra']
                        }
                    )
                    
                    # Se o ingrediente já existia, atualiza o preço e status de extra
                    if not created:
                        ingredient.price = ing_data['price']
                        ingredient.is_extra = group_data['is_extra']
                        ingredient.save()
                    
                    # Cria o ProductIngredient com o grupo específico do produto
                    pi = ProductIngredient.objects.create(
                        product=product,
                        ingredient=ingredient,
                        group_name=group_name,  # Usando o nome do grupo diretamente
                        is_required=group_data['is_required'],
                        max_quantity=group_data['max_quantity'],
                        is_extra=group_data['is_extra'],
                        price=ing_data['price']
                    )
                    print(f"DEBUG: ProductIngredient criado - preço salvo: {pi.price} (tipo: {type(pi.price)})")
                    print(f"ProductIngredient criado: {product.name} - {group_name} - {ingredient.name} (extra: {ingredient.is_extra}, preço: {ingredient.price})")
                    
                except Exception as e:
                    print(f"Erro ao criar ProductIngredient: {str(e)}")
                    continue

    def perform_update(self, serializer):
        """
        Atualiza um produto existente e seus ingredientes.
        """
        print("Iniciando atualização do produto...")
        # Primeiro, salva as alterações do produto
        product = serializer.save()
        print(f"Produto salvo: {product.name}")
        
        # Processa os novos ingredientes
        ingredients = []
        for key in self.request.data:
            if key.startswith('ingredients['):
                ingredients.append(self.request.data[key])
        
        print(f"Total de ingredientes recebidos: {len(ingredients)}")
        
        if ingredients:  # Só remove e recria se houver novos ingredientes
            # Remove todos os ingredientes existentes deste produto específico
            ProductIngredient.objects.filter(product=product).delete()
            print("Ingredientes antigos removidos")
            
            # Agrupa ingredientes por grupo para garantir consistência
            group_map = {}
            for ing_data in ingredients:
                try:
                    ing_obj = json.loads(ing_data)
                    ing_name = ing_obj.get('name')
                    group_name = ing_obj.get('groupName')  # Mudando de category para groupName
                    is_required = ing_obj.get('isRequired', False)
                    max_quantity = ing_obj.get('maxQuantity', 1)
                    is_extra = bool(ing_obj.get('isExtra', False))
                    price = ing_obj.get('price', 0)
                    print(f"DEBUG UPDATE: Ingrediente {ing_name} - preço recebido: {price} (tipo: {type(price)})")
                    
                    if not ing_name or not group_name:
                        print("Nome do ingrediente ou grupo vazio, pulando...")
                        continue
                    
                    print(f"Processando ingrediente: {ing_name} (grupo: {group_name}, extra: {is_extra}, preço: {price})")
                    
                    # Organiza por grupo
                    if group_name not in group_map:
                        group_map[group_name] = {
                            'is_required': is_required,
                            'max_quantity': max_quantity,
                            'is_extra': is_extra,
                            'ingredients': []
                        }
                    group_map[group_name]['ingredients'].append({
                        'name': ing_name,
                        'price': price
                    })
                    print(f"DEBUG UPDATE: Adicionado ao grupo {group_name}: {ing_name} com preço {price}")
                    
                except Exception as e:
                    print(f"Erro ao processar ingrediente: {str(e)}")
                    continue
            
            # Processa cada grupo
            for group_name, group_data in group_map.items():
                for ing_data in group_data['ingredients']:
                    try:
                        # Cria ou obtém o ingrediente
                        ingredient, created = Ingredient.objects.get_or_create(
                            name=ing_data['name'],
                            defaults={
                                'category': None,
                                'price': ing_data['price'],
                                'is_extra': group_data['is_extra']
                            }
                        )
                        
                        # Se o ingrediente já existia, atualiza o preço e status de extra
                        if not created:
                            ingredient.price = ing_data['price']
                            ingredient.is_extra = group_data['is_extra']
                            ingredient.save()
                        
                        # Cria o ProductIngredient com o grupo específico do produto
                        pi = ProductIngredient.objects.create(
                            product=product,
                            ingredient=ingredient,
                            group_name=group_name,  # Usando o nome do grupo diretamente
                            is_required=group_data['is_required'],
                            max_quantity=group_data['max_quantity'],
                            is_extra=group_data['is_extra'],
                            price=ing_data['price']
                        )
                        print(f"DEBUG UPDATE: ProductIngredient criado - preço salvo: {pi.price} (tipo: {type(pi.price)})")
                        print(f"ProductIngredient criado: {product.name} - {group_name} - {ingredient.name} (extra: {ingredient.is_extra}, preço: {ingredient.price})")
                        
                    except Exception as e:
                        print(f"Erro ao criar ProductIngredient: {str(e)}")
                        continue
        else:
            print("Nenhum ingrediente recebido, mantendo os existentes")

    @action(detail=True, methods=['post'])
    def add_ingredient(self, request, pk=None):
        """
        Adiciona um ingrediente a um produto.
        """
        product = self.get_object()
        ingredient_id = request.data.get('ingredient_id')
        is_removable = request.data.get('is_removable', False)
        is_addable = request.data.get('is_addable', True)

        try:
            ingredient = Ingredient.objects.get(
                id=ingredient_id
            )
        except Ingredient.DoesNotExist:
            return Response(
                {'error': 'Ingrediente não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        product_ingredient, created = ProductIngredient.objects.get_or_create(
            product=product,
            ingredient=ingredient,
            defaults={
                'is_removable': is_removable,
                'is_addable': is_addable
            }
        )

        if not created:
            product_ingredient.is_removable = is_removable
            product_ingredient.is_addable = is_addable
            product_ingredient.save()

        serializer = ProductIngredientSerializer(product_ingredient)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def remove_ingredient(self, request, pk=None):
        """
        Remove um ingrediente de um produto.
        """
        product = self.get_object()
        ingredient_id = request.data.get('ingredient_id')

        try:
            ingredient = Ingredient.objects.get(
                id=ingredient_id
            )
        except Ingredient.DoesNotExist:
            return Response(
                {'error': 'Ingrediente não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            product_ingredient = ProductIngredient.objects.get(
                product=product,
                ingredient=ingredient
            )
            product_ingredient.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProductIngredient.DoesNotExist:
            return Response(
                {'error': 'Ingrediente não encontrado no produto'},
                status=status.HTTP_404_NOT_FOUND
            )

class IngredientViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de ingredientes.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer

    def get_queryset(self):
        return Ingredient.objects.all()

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Retorna todos os ingredientes disponíveis.
        """
        ingredients = Ingredient.objects.all()
        serializer = IngredientSerializer(ingredients, many=True)
        return Response(serializer.data)

class PromotionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento de promoções.
    """
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer

    def get_serializer_class(self):
        """
        Retorna o serializer apropriado baseado na ação.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return PromotionCreateSerializer
        return PromotionSerializer

    def get_queryset(self):
        """
        Retorna a lista de promoções, filtrando por status se necessário.
        """
        queryset = Promotion.objects.filter(restaurant=self.request.user.settings)
        show_inactive = self.request.query_params.get('show_inactive', 'false').lower() == 'true'
        if not show_inactive:
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def update(self, request, *args, **kwargs):
        print("Dados recebidos na atualização:", request.data)
        print("Arquivos recebidos:", request.FILES)
        print("Content-Type:", request.content_type)
        return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        print("Dados recebidos na criação:", request.data)
        print("Arquivos recebidos:", request.FILES)
        print("Content-Type:", request.content_type)
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        Ativa ou desativa uma promoção.
        """
        promotion = self.get_object()
        promotion.is_active = not promotion.is_active
        promotion.save()
        
        return Response({
            'id': promotion.id,
            'name': promotion.name,
            'is_active': promotion.is_active
        })
