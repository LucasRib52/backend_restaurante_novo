from django.db import models
from orders.models import Order

class DailyStats(models.Model):
    """
    Modelo que armazena estatísticas diárias.
    Usado para gerar relatórios e gráficos no dashboard.
    """
    date = models.DateField(verbose_name='Data')
    total_orders = models.PositiveIntegerField(default=0, verbose_name='Total de Pedidos')
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Receita Total')
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Ticket Médio')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estatística Diária'
        verbose_name_plural = 'Estatísticas Diárias'
        unique_together = ['date']
        ordering = ['-date']

    def __str__(self):
        return f"Estatísticas - {self.date}"

class ProductStats(models.Model):
    """
    Modelo que armazena estatísticas de produtos mais vendidos.
    Usado para gerar relatórios de produtos populares.
    """
    product_name = models.CharField(max_length=100, verbose_name='Nome do Produto')
    total_quantity = models.PositiveIntegerField(default=0, verbose_name='Quantidade Total Vendida')
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Receita Total')
    period_start = models.DateField(verbose_name='Início do Período')
    period_end = models.DateField(verbose_name='Fim do Período')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estatística de Produto'
        verbose_name_plural = 'Estatísticas de Produtos'
        ordering = ['-total_quantity']

    def __str__(self):
        return f"{self.product_name} - {self.period_start} até {self.period_end}"

class CategoryStats(models.Model):
    """
    Modelo que armazena estatísticas por categoria.
    Usado para gerar relatórios de categorias mais populares.
    """
    category_name = models.CharField(max_length=100, verbose_name='Nome da Categoria')
    total_orders = models.PositiveIntegerField(default=0, verbose_name='Total de Pedidos')
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Receita Total')
    period_start = models.DateField(verbose_name='Início do Período')
    period_end = models.DateField(verbose_name='Fim do Período')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Estatística de Categoria'
        verbose_name_plural = 'Estatísticas de Categorias'
        ordering = ['-total_revenue']

    def __str__(self):
        return f"{self.category_name} - {self.period_start} até {self.period_end}"
