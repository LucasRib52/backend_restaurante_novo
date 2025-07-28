from rest_framework import serializers
from .models import ClientOrder
from orders.models import Order, OrderItem, OrderItemIngredient
from products.models import Ingredient, ProductIngredient

class ClientOrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criar um novo pedido de cliente.
    """
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    payment_method = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    change_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)

    class Meta:
        model = ClientOrder
        fields = ('customer_name', 'customer_phone', 'customer_address', 'notes', 'items', 'total_amount', 'payment_method', 'change_amount')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        """
        Cria um novo pedido com seus itens e ingredientes.
        """
        # Extrair dados do cliente e do pedido
        items_data = validated_data.pop('items')
        total_amount = validated_data.pop('total_amount', 0)
        payment_method = validated_data.pop('payment_method', None)
        change_amount = validated_data.pop('change_amount', None)
        # Dados do cliente
        customer_name = validated_data.pop('customer_name')
        customer_phone = validated_data.pop('customer_phone')
        customer_address = validated_data.pop('customer_address')
        notes = validated_data.pop('notes', '')
        
        restaurant = self.context.get('restaurant')
        # Criar o pedido principal com todos os campos obrigatórios
        order = Order.objects.create(
            restaurant=restaurant,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_address=customer_address,
            notes=notes,
            total_amount=total_amount,
            payment_method=payment_method,
            change_amount=change_amount
        )
        
        # Criar o pedido do cliente
        client_order = ClientOrder.objects.create(
            order=order,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_address=customer_address,
            notes=notes,
            total_amount=total_amount,
            payment_method=payment_method,
            change_amount=change_amount
        )
        
        # Criar os itens do pedido
        for item_data in items_data:
            order_item = OrderItem.objects.create(
                order=order,
                product_name=item_data.get('product_name', 'Produto'),
                quantity=item_data.get('quantity', 1),
                unit_price=item_data.get('unit_price', 0),
                notes=item_data.get('notes', '')
            )
            
            # Adicionar ingredientes se houver
            if 'ingredients' in item_data:
                for ingredient_data in item_data.get('ingredients', []):
                    try:
                        ingrediente = Ingredient.objects.get(id=ingredient_data['ingredient'])
                    except Ingredient.DoesNotExist:
                        continue
                    # Busca ProductIngredient específico para o grupo (se informado)
                    group_name_input = ingredient_data.get('group_name') or ingredient_data.get('groupName')
                    pi_qs = ProductIngredient.objects.filter(product_id=ingredient_data.get('product_id'), ingredient=ingrediente) if ingredient_data.get('product_id') else None
                    if pi_qs and group_name_input:
                        pi_qs = pi_qs.filter(group_name__iexact=group_name_input.strip())
                    if pi_qs and ingredient_data.get('is_extra'):
                        first_pi = pi_qs.first()
                        if first_pi and not first_pi.is_extra:
                            first_pi.is_extra = True
                            first_pi.save(update_fields=['is_extra'])

                    # Cria ou obtém OrderItemIngredient
                    group_for_item = (pi_qs.first().group_name if (pi_qs and pi_qs.first()) else (group_name_input or 'Auto')).strip()
                    oi, created = OrderItemIngredient.objects.get_or_create(
                        order_item=order_item,
                        ingredient=ingrediente,
                        group_name=group_for_item,
                        is_extra=ingredient_data.get('is_extra', False),
                        defaults={
                            'is_added': ingredient_data.get('is_added', True),
                            'price': ingredient_data.get('price', ingrediente.price or 0)
                        }
                    )
                    if not created:
                        oi.is_added = ingredient_data.get('is_added', True)
                        oi.price = ingredient_data.get('price', ingrediente.price or 0)
                        oi.is_extra = ingredient_data.get('is_extra', oi.is_extra)
                        oi.save()
        
        return client_order 