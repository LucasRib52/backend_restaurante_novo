from django.core.management.base import BaseCommand
from orders.models import OrderItem
from products.models import Product

class Command(BaseCommand):
    help = 'Atualiza pedidos antigos associando o produto correto baseado no product_name'

    def handle(self, *args, **options):
        # Busca todos os OrderItems que não têm produto associado
        items_sem_produto = OrderItem.objects.filter(product__isnull=True)
        self.stdout.write(f'Encontrados {items_sem_produto.count()} itens sem produto associado')

        atualizados = 0
        for item in items_sem_produto:
            # Tenta encontrar o produto pelo nome
            try:
                produto = Product.objects.get(name__iexact=item.product_name)
                item.product = produto
                item.save()
                atualizados += 1
                self.stdout.write(f'Atualizado item {item.id}: {item.product_name} -> {produto.name}')
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Produto não encontrado para item {item.id}: {item.product_name}'))
            except Product.MultipleObjectsReturned:
                self.stdout.write(self.style.WARNING(f'Múltiplos produtos encontrados para item {item.id}: {item.product_name}'))

        self.stdout.write(self.style.SUCCESS(f'Atualizados {atualizados} itens com sucesso!')) 