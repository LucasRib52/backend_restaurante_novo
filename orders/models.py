from django.db import models
from products.models import Product, Ingredient, Promotion
from settings.models import Settings  # import para multi-tenancy

class Order(models.Model):
    """
    Modelo que representa um pedido.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('confirmed', 'Confirmado'),
        ('preparing', 'Preparando'),
        ('ready', 'Pronto'),
        ('delivered', 'Entregue'),
        ('cancelled', 'Cancelado'),
    ]

    restaurant = models.ForeignKey(Settings, on_delete=models.CASCADE, related_name='orders')  # separação por empresa
    order_number = models.PositiveIntegerField(verbose_name='Número do Pedido', null=True, blank=True)
    customer_name = models.CharField(max_length=100, verbose_name='Nome do Cliente')
    customer_phone = models.CharField(max_length=20, verbose_name='Telefone do Cliente')
    customer_address = models.CharField(max_length=200, blank=True, verbose_name='Endereço do Cliente')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Status')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Valor Total')
    notes = models.TextField(blank=True, verbose_name='Observações')
    payment_method = models.CharField(max_length=30, blank=True, null=True, verbose_name='Forma de Pagamento')
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Troco para')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']

    def __str__(self):
        return f"Pedido #{self.order_number or self.id} - {self.customer_name}"

    def save(self, *args, **kwargs):
        # Se não tem order_number, gera a sequência baseada na quantidade de pedidos da empresa
        if not self.order_number:
            total = Order.objects.filter(restaurant=self.restaurant).count()
            self.order_number = total + 1
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    """
    Modelo que representa um item de pedido.
    """
    ITEM_TYPE_CHOICES = [
        ('regular', 'Produto Regular'),
        ('promotion', 'Item de Promoção'),
        ('reward', 'Brinde de Promoção'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    promotion = models.ForeignKey(Promotion, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default='regular', verbose_name='Tipo do Item')
    product_name = models.CharField(max_length=100, default='Produto', verbose_name='Nome do Produto')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantidade')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço Unitário')
    notes = models.CharField(max_length=200, blank=True, verbose_name='Observações')
    customization_details = models.JSONField(null=True, blank=True, verbose_name='Detalhes de Personalização')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Item de Pedido'
        verbose_name_plural = 'Itens de Pedido'

    def __str__(self):
        if self.item_type == 'promotion':
            return f"{self.product_name} (Promoção) x {self.quantity}"
        elif self.item_type == 'reward':
            return f"{self.product_name} (Brinde) x {self.quantity}"
        return f"{self.product_name} x {self.quantity}"

class OrderItemIngredient(models.Model):
    """
    Modelo que representa as personalizações de ingredientes em um item do pedido.
    """
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    group_name = models.CharField(max_length=100, blank=True, verbose_name='Grupo do Produto')
    is_extra = models.BooleanField(default=False, verbose_name='É Extra')
    is_added = models.BooleanField(default=True, verbose_name='Adicionado')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ingrediente do Item'
        verbose_name_plural = 'Ingredientes do Item'
        unique_together = ['order_item', 'ingredient', 'group_name', 'is_extra']

    def __str__(self):
        action = "Adicionado" if self.is_added else "Removido"
        return f"{self.ingredient.name} ({action})"
