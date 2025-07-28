from django.db import models
from django.core.validators import MinValueValidator
from settings.models import Settings  # import para multi-tenancy

class Category(models.Model):
    """
    Modelo que representa uma categoria de produtos.
    """
    name = models.CharField(max_length=100, verbose_name='Nome')
    emoji = models.CharField(max_length=2, blank=True, default='', verbose_name='Emoji')
    description = models.TextField(blank=True, verbose_name='Descrição')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    restaurant = models.ForeignKey(Settings, on_delete=models.CASCADE, related_name='categories')  # separação por empresa

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    """
    Modelo que representa um produto.
    """
    name = models.CharField(max_length=100, verbose_name='Nome')
    description = models.TextField(verbose_name='Descrição')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Imagem')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name='Categoria')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    restaurant = models.ForeignKey(Settings, on_delete=models.CASCADE, related_name='products')

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['name']

    def __str__(self):
        return self.name

class IngredientCategory(models.Model):
    """
    Modelo que representa uma subcategoria de ingredientes (ex: Molhos, Proteínas, etc).
    """
    name = models.CharField(max_length=100, verbose_name='Nome da Subcategoria')
    description = models.TextField(blank=True, verbose_name='Descrição')
    is_extra = models.BooleanField(default=False, verbose_name='É Extra')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Subcategoria de Ingrediente'
        verbose_name_plural = 'Subcategorias de Ingredientes'
        ordering = ['name']

    def __str__(self):
        return self.name

class Ingredient(models.Model):
    """
    Modelo que representa um ingrediente.
    """
    name = models.CharField(max_length=100, verbose_name='Nome')
    description = models.TextField(blank=True, verbose_name='Descrição')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Preço')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    is_extra = models.BooleanField(default=False, verbose_name='É Extra')
    category = models.ForeignKey(IngredientCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='ingredients', verbose_name='Subcategoria')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ingrediente'
        verbose_name_plural = 'Ingredientes'
        ordering = ['name']

    def __str__(self):
        return self.name

class ProductIngredient(models.Model):
    """
    Modelo que relaciona produtos com ingredientes.
    Permite definir quais ingredientes podem ser adicionados/removidos de cada produto.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ingredients')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    group_name = models.CharField(max_length=100, verbose_name='Grupo do Produto')
    is_required = models.BooleanField(default=False)
    max_quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Preço Extra')
    is_extra = models.BooleanField(default=False, verbose_name='É Extra')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ingrediente do Produto'
        verbose_name_plural = 'Ingredientes dos Produtos'

    def __str__(self):
        return f"{self.product.name} - {self.group_name} - {self.ingredient.name}"

class Promotion(models.Model):
    """
    Modelo que representa uma promoção.
    Exemplo: Compre 3 saladas por R$ 45 e ganhe uma salada de brinde
    """
    name = models.CharField(max_length=100, verbose_name='Nome')
    description = models.TextField(verbose_name='Descrição')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço')
    image = models.ImageField(upload_to='promotions/', blank=True, null=True, verbose_name='Imagem')
    is_active = models.BooleanField(default=True, verbose_name='Ativa')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    restaurant = models.ForeignKey(Settings, on_delete=models.CASCADE, related_name='promotions')

    class Meta:
        verbose_name = 'Promoção'
        verbose_name_plural = 'Promoções'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class PromotionItem(models.Model):
    """
    Modelo que representa um produto que faz parte da promoção.
    Exemplo: As 3 saladas que o cliente precisa comprar
    """
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='promotions')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Quantidade')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Item da Promoção'
        verbose_name_plural = 'Itens da Promoção'

    def __str__(self):
        return f"{self.quantity}x {self.product.name} em {self.promotion.name}"

class PromotionReward(models.Model):
    """
    Modelo que representa um produto que pode ser escolhido como brinde.
    Exemplo: A salada que o cliente ganha de brinde
    """
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='rewards')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reward_promotions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Brinde da Promoção'
        verbose_name_plural = 'Brindes da Promoção'

    def __str__(self):
        return f"{self.product.name} como brinde em {self.promotion.name}"
