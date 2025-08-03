from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Order, OrderItem, OrderItemIngredient
from products.serializers import ProductSerializer, IngredientSerializer
from products.models import Product, Ingredient, ProductIngredient

class OrderItemIngredientSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo OrderItemIngredient.
    Inclui informações do ingrediente relacionado.
    """
    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        write_only=True,
        source='ingredient'
    )
    group_name = serializers.SerializerMethodField()
    is_extra = serializers.BooleanField(read_only=True)

    class Meta:
        model = OrderItemIngredient
        fields = ('id', 'order_item', 'ingredient', 'ingredient_id',
                 'is_added', 'price', 'created_at', 'updated_at', 'group_name', 'is_extra')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_group_name(self, obj):
        # Prioridade: campo persistido no modelo
        if obj.group_name:
            return obj.group_name
        """
        Retorna o nome do grupo do ingrediente.
        Prioriza ProductIngredient.group_name, depois extras como 'Extras', depois categoria do ingrediente, depois 'Outros'.
        """
        try:
            # Tenta usar o produto associado ao item
            product = obj.order_item.product
            if not product:
                # Associa dinamicamente se possível
                product_name = obj.order_item.product_name
                product = Product.objects.filter(name__iexact=product_name).first()
                if product:
                    print(f"[AUTO-FIX] Produto associado dinamicamente para OrderItem {obj.order_item.id}: {product.name}")
            # Busca associação de ingrediente no produto
            try:
                pi = ProductIngredient.objects.filter(product=product, ingredient=obj.ingredient).first()
                if pi:
                    print(f"[DEBUG] Produto: {product.name}, Ingrediente: {obj.ingredient.name}, Grupo: {pi.group_name}")
                    return pi.group_name
                else:
                    raise ProductIngredient.DoesNotExist
            except ProductIngredient.DoesNotExist:
                # Ingrediente extra sem grupo definido
                if obj.ingredient and obj.ingredient.is_extra:
                    print(f"[DEBUG] Ingrediente {obj.ingredient.name} é extra mas sem grupo definido, usando 'Extras'")
                    return 'Extras'
                # Agrupa pela categoria do ingrediente
                if obj.ingredient and obj.ingredient.category:
                    print(f"[DEBUG] Grupo não encontrado, usando categoria do ingrediente como grupo: {obj.ingredient.category.name}")
                    return obj.ingredient.category.name
                # Fallback geral
                print(f"[DEBUG] Grupo não encontrado e sem categoria, usando 'Outros'")
                return 'Outros'
        except Exception as e:
            print(f"[DEBUG] Erro ao buscar group_name: {e}, fallback para categoria ou 'Outros'")
            if obj.ingredient and obj.ingredient.is_extra:
                return 'Extras'
            if obj.ingredient and obj.ingredient.category:
                return obj.ingredient.category.name
            return 'Outros'

    # is_extra vem direto do modelo agora, portanto não precisamos mais de lógica adicional.

class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo OrderItem.
    Inclui informações do produto e ingredientes personalizados.
    """
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
        source='product'
    )
    product_name = serializers.CharField(read_only=True)
    ingredients = OrderItemIngredientSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    promotion = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'product', 'product_id', 'product_name', 'quantity',
                 'unit_price', 'notes', 'ingredients', 'total_price', 'item_type', 'promotion',
                 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_total_price(self, obj):
        """
        Calcula o preço total do item incluindo ingredientes personalizados.
        """
        base_price = obj.unit_price * obj.quantity
        ingredients_price = sum(ing.price for ing in obj.ingredients.all())
        return base_price + ingredients_price

class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Order.
    Inclui informações dos itens do pedido.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    customer_address = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    change_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    id = serializers.SerializerMethodField()  # Sobrescrever o ID para usar order_number

    class Meta:
        model = Order
        fields = ('id', 'order_number', 'customer_name', 'customer_phone', 'customer_address', 'status', 'status_display', 'total_amount',
                 'notes', 'items', 'created_at', 'updated_at', 'payment_method', 'change_amount')
        read_only_fields = ('order_number', 'created_at', 'updated_at')

    def get_id(self, obj):
        return obj.order_number or obj.id

    def get_customer_name(self, obj):
        if hasattr(obj, 'client_order'):
            return obj.client_order.customer_name
        return None

    def get_customer_phone(self, obj):
        if hasattr(obj, 'client_order'):
            return obj.client_order.customer_phone
        return None

    def get_customer_address(self, obj):
        if hasattr(obj, 'client_order'):
            return obj.client_order.customer_address
        return None

class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criar um novo pedido.
    Inclui validações e cálculos automáticos.
    """
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    payment_method = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    change_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = Order
        fields = ('customer_name', 'customer_phone', 'customer_address', 'notes', 'items', 'total_amount', 'payment_method', 'change_amount')
        read_only_fields = ('id', 'created_at', 'updated_at', 'status')

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        total_amount = validated_data.pop('total_amount', 0)
        payment_method = validated_data.get('payment_method')
        change_amount = validated_data.get('change_amount')
        
        # Validação extra: todo item deve ter product_id
        for idx, item in enumerate(items_data):
            if not item.get('product_id'):
                raise ValidationError(f"O item {idx+1} do pedido está sem produto associado (product_id). Corrija antes de prosseguir.")
        
        print("[DEBUG] Criando pedido com items:", items_data)
        
        order = Order.objects.create(
            **validated_data,
            total_amount=total_amount,
            status='pending',
            payment_method=payment_method,
            change_amount=change_amount
        )
        
        for item_data in items_data:
            # Buscar o produto correto
            product_id = item_data.get('product_id')
            print(f"[DEBUG] Processando item. product_id recebido: {product_id}")
            
            try:
                product_obj = Product.objects.get(id=product_id)
                print(f"[DEBUG] Produto encontrado: {product_obj.name} (id: {product_obj.id})")
                
                # --- PATCH: CAMPOS DE PROMOÇÃO ---
                promotion_id = item_data.get('promotion_id')
                item_type = item_data.get('item_type', 'regular')
                customization_details = item_data.get('customization_details')
                promotion_obj = None
                if promotion_id:
                    from products.models import Promotion
                    try:
                        promotion_obj = Promotion.objects.get(id=promotion_id)
                    except Promotion.DoesNotExist:
                        promotion_obj = None
                # ----------------------------------

                # Criar o item do pedido com o produto associado
                order_item = OrderItem.objects.create(
                    order=order,
                    product=product_obj,  # Garantindo que o produto seja associado
                    product_name=product_obj.name,  # Usando o nome do produto do banco
                    quantity=item_data.get('quantity', 1),
                    unit_price=item_data.get('unit_price', 0),
                    notes=item_data.get('notes', ''),
                    # PATCH: campos de promoção
                    promotion=promotion_obj,
                    item_type=item_type,
                    customization_details=customization_details
                )
                print(f"[DEBUG] OrderItem criado: id={order_item.id}, product={order_item.product}, product_name={order_item.product_name}, item_type={order_item.item_type}, promotion={order_item.promotion}, customization_details={order_item.customization_details}")
                
                # Adicionar ingredientes se houver
                if 'ingredients' in item_data:
                    print(f"[DEBUG] Processando {len(item_data['ingredients'])} ingredientes")
                    for ingredient_data in item_data['ingredients']:
                        try:
                            ingrediente = Ingredient.objects.get(id=ingredient_data['ingredient'])
                            print(f"[DEBUG] Ingrediente encontrado: {ingrediente.name} (id: {ingrediente.id})")
                            
                            # Tenta buscar o grupo correto informado no payload
                            group_name_input = ingredient_data.get('group_name') or ingredient_data.get('groupName')
                            pi_qs = ProductIngredient.objects.filter(product=product_obj, ingredient=ingrediente)
                            if group_name_input:
                                pi_qs = pi_qs.filter(group_name__iexact=group_name_input.strip())
                            pi = pi_qs.first()

                            if pi:
                                # Atualiza flag extra se veio marcada no payload e não estiver no banco
                                if ingredient_data.get('is_extra') and not pi.is_extra:
                                    pi.is_extra = True
                                    pi.save(update_fields=['is_extra'])
                                print(f"[DEBUG] Grupo do ingrediente encontrado: {pi.group_name}")
                            else:
                                # Fallback: cria automaticamente usando group_name_input ou 'Auto'
                                auto_group = group_name_input or 'Auto'
                                print(f"[DEBUG] AVISO: Ingrediente {ingrediente.name} não encontrado no produto {product_obj.name} para grupo '{auto_group}', criando ProductIngredient automaticamente!")
                                pi = ProductIngredient.objects.create(
                                    product=product_obj,
                                    ingredient=ingrediente,
                                    group_name=auto_group,
                                    is_required=False,
                                    max_quantity=1,
                                    is_extra=ingredient_data.get('is_extra', False)
                                )
                            
                            group_for_item = (pi.group_name if pi else (group_name_input or 'Auto')).strip()
                            OrderItemIngredient.objects.create(
                                order_item=order_item,
                                ingredient=ingrediente,
                                group_name=group_for_item,
                                is_extra=ingredient_data.get('is_extra', False),
                                is_added=ingredient_data.get('is_added', True),
                                price=ingredient_data.get('price', ingrediente.price or 0)
                            )
                        except Ingredient.DoesNotExist:
                            print(f"[DEBUG] ERRO: Ingrediente não encontrado com id: {ingredient_data['ingredient']}")
                            continue
            except Product.DoesNotExist:
                print(f"[DEBUG] ERRO: Produto não encontrado com id: {product_id}")
                continue
                
        return order

class OrderUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualizar o status de um pedido.
    """
    class Meta:
        model = Order
        fields = ('status', 'notes') 