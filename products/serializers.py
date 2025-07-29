from rest_framework import serializers
from .models import Category, Product, Ingredient, ProductIngredient, IngredientCategory, Promotion, PromotionItem, PromotionReward
from django.conf import settings as django_settings
import json

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Category.
    """
    class Meta:
        model = Category
        fields = ('id', 'name', 'emoji', 'description', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class IngredientCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IngredientCategory
        fields = ('id', 'name', 'description')

class IngredientSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Ingredient.
    """
    category = IngredientCategorySerializer(read_only=True)
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'price', 'category', 'is_extra']

class ProductIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ProductIngredient
        fields = ['id', 'ingredient', 'group_name', 'is_required', 'max_quantity', 'is_extra', 'price']

class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Product.
    Inclui informações da categoria e ingredientes disponíveis.
    """
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        source='category'
    )
    available_ingredients = ProductIngredientSerializer(many=True, read_only=True, source='ingredients')

    class Meta:
        model = Product
        fields = ('id', 'category', 'category_id', 'name',
                 'description', 'price', 'image', 'is_active',
                 'available_ingredients', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def to_representation(self, instance):
        """
        Sobrescreve o método para garantir que os ingredientes sejam retornados corretamente.
        """
        representation = super().to_representation(instance)
        # Garante que available_ingredients seja uma lista vazia se não houver ingredientes
        if not representation.get('available_ingredients'):
            representation['available_ingredients'] = []
        return representation

class ProductDetailSerializer(ProductSerializer):
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields

    def get_total_orders(self, obj):
        """
        Retorna o total de pedidos que incluem este produto.
        """
        return obj.orderitem_set.count()

    def get_total_revenue(self, obj):
        """
        Retorna a receita total gerada por este produto.
        """
        return sum(item.unit_price * item.quantity for item in obj.orderitem_set.all())

class PromotionItemSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo PromotionItem.
    Inclui informações do produto relacionado.
    """
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
        source='product'
    )

    class Meta:
        model = PromotionItem
        fields = ('id', 'promotion', 'product', 'product_id', 'quantity', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class PromotionRewardSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo PromotionReward.
    Inclui informações do produto que pode ser escolhido como brinde.
    """
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        write_only=True,
        source='product'
    )

    class Meta:
        model = PromotionReward
        fields = ('id', 'promotion', 'product', 'product_id', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class PromotionSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Promotion.
    Inclui informações dos itens e brindes disponíveis.
    """
    items = PromotionItemSerializer(many=True, read_only=True)
    rewards = PromotionRewardSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Promotion
        fields = ('id', 'name', 'description', 'price', 'image', 'is_active',
                 'items', 'rewards', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return f"{django_settings.MEDIA_URL}{obj.image}"
        return None

    def get_savings_amount(self, obj):
        """
        Calcula quanto o cliente economiza com a promoção.
        """
        total_regular_price = sum(
            item.product.price * item.quantity
            for item in obj.items.all()
        )
        return total_regular_price - obj.price

class PromotionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criar e atualizar uma promoção.
    Permite definir os itens e brindes da promoção.
    """
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )
    rewards = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Promotion
        fields = ('name', 'description', 'price', 'is_active', 'items', 'rewards', 'image')

    def to_internal_value(self, data):
        print("Dados recebidos no serializer (raw):", data)
        print("Tipo dos dados:", type(data))
        
        # Converte os dados para um dicionário mutável
        mutable_data = {}
        for key, value in data.items():
            if key == 'image':
                # Trata o campo image - remove se for uma URL (já existe)
                image_value = value[0] if isinstance(value, list) else value
                if isinstance(image_value, str) and (image_value.startswith('http://') or image_value.startswith('https://')):
                    print("Removendo campo image que é uma URL existente")
                    continue  # Não adiciona ao mutable_data
                elif image_value == '' or image_value is None:
                    print("Removendo campo image vazio")
                    continue  # Não adiciona ao mutable_data
                else:
                    mutable_data[key] = value
            elif key == 'price':
                try:
                    mutable_data[key] = float(value[0] if isinstance(value, list) else value)
                except (ValueError, TypeError):
                    print(f"Erro ao converter price: {value}")
                    raise serializers.ValidationError({'price': 'Preço inválido'})
            elif key == 'is_active':
                mutable_data[key] = (value[0] if isinstance(value, list) else value).lower() == 'true'
            elif key in ['items', 'rewards']:
                # Aceita listas de dicionários diretamente
                if isinstance(value, list) and (not value or isinstance(value[0], dict)):
                    mutable_data[key] = value
                else:
                    try:
                        value_str = value[0] if isinstance(value, list) else value
                        mutable_data[key] = json.loads(value_str)
                    except (TypeError, json.JSONDecodeError):
                        raise serializers.ValidationError({key: 'Formato inválido'})
            else:
                mutable_data[key] = value[0] if isinstance(value, list) else value

        print("Dados processados:", mutable_data)

        # Validação básica dos campos
        if not mutable_data.get('name'):
            raise serializers.ValidationError({'name': 'Nome é obrigatório'})
        if not mutable_data.get('description'):
            raise serializers.ValidationError({'description': 'Descrição é obrigatória'})
        if mutable_data.get('price') is None:
            raise serializers.ValidationError({'price': 'Preço é obrigatório'})
        
        # Validação de items e rewards apenas se fornecidos (para atualização)
        items = mutable_data.get('items')
        rewards = mutable_data.get('rewards')
        
        if items is not None and not items:
            raise serializers.ValidationError({'items': 'Adicione pelo menos um item'})
        if rewards is not None and not rewards:
            raise serializers.ValidationError({'rewards': 'Adicione pelo menos um brinde'})

        # Validação dos itens
        for item in mutable_data.get('items', []):
            if not isinstance(item, dict):
                raise serializers.ValidationError({'items': 'Formato inválido dos itens'})
            if 'product_id' not in item:
                raise serializers.ValidationError({'items': 'ID do produto é obrigatório'})
            if 'quantity' not in item:
                raise serializers.ValidationError({'items': 'Quantidade é obrigatória'})

        # Validação dos brindes
        for reward in mutable_data.get('rewards', []):
            if not isinstance(reward, dict):
                raise serializers.ValidationError({'rewards': 'Formato inválido dos brindes'})
            if 'product_id' not in reward:
                raise serializers.ValidationError({'rewards': 'ID do produto é obrigatório'})

        return super().to_internal_value(mutable_data)

    def create(self, validated_data):
        print("Dados validados na criação:", validated_data)
        items_data = validated_data.pop('items', [])
        rewards_data = validated_data.pop('rewards', [])
        image = validated_data.pop('image', None)
        
        # Adiciona o restaurant do usuário logado
        validated_data['restaurant'] = self.context['request'].user.settings
        
        try:
            promotion = Promotion.objects.create(**validated_data)
            
            if image:
                promotion.image = image
                promotion.save()
            
            # Criar os itens da promoção
            for item_data in items_data:
                PromotionItem.objects.create(
                    promotion=promotion,
                    product_id=item_data['product_id'],
                    quantity=item_data.get('quantity', 1)
                )
            
            # Criar os brindes disponíveis
            for reward_data in rewards_data:
                PromotionReward.objects.create(
                    promotion=promotion,
                    product_id=reward_data['product_id']
                )
            
            return promotion
        except Exception as e:
            print("Erro ao criar promoção:", str(e))
            raise

    def update(self, instance, validated_data):
        print("Dados validados na atualização:", validated_data)
        items_data = validated_data.pop('items', None)
        rewards_data = validated_data.pop('rewards', None)
        image = validated_data.pop('image', None)

        try:
            print("Atualizando promoção:", instance.id)
            print("Items data:", items_data)
            print("Rewards data:", rewards_data)
            
            # Atualiza campos simples
            for attr, value in validated_data.items():
                print(f"Atualizando campo {attr}: {value}")
                setattr(instance, attr, value)

            # Atualiza a imagem se fornecida
            if image is not None:
                print("Atualizando imagem")
                instance.image = image

            instance.save()
            print("Promoção salva com sucesso")

            # Atualiza itens da promoção
            if items_data is not None:
                print("Atualizando itens da promoção")
                instance.items.all().delete()
                for item_data in items_data:
                    print(f"Criando item: {item_data}")
                    PromotionItem.objects.create(
                        promotion=instance,
                        product_id=item_data['product_id'],
                        quantity=item_data.get('quantity', 1)
                    )

            # Atualiza brindes da promoção
            if rewards_data is not None:
                print("Atualizando brindes da promoção")
                instance.rewards.all().delete()
                for reward_data in rewards_data:
                    print(f"Criando brinde: {reward_data}")
                    PromotionReward.objects.create(
                        promotion=instance,
                        product_id=reward_data['product_id']
                    )

            print("Atualização concluída com sucesso")
            return instance
        except Exception as e:
            print("Erro ao atualizar promoção:", str(e))
            import traceback
            traceback.print_exc()
            raise 