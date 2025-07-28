from django.db import models
from settings.models import Settings

# Create your models here.

class Plan(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Nome do Plano')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Preço')
    duration_days = models.IntegerField(verbose_name='Duração em Dias')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'

    def __str__(self):
        return self.name


class Subscription(models.Model):
    company = models.ForeignKey(Settings, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=50, default='free', verbose_name='Plano')
    start_date = models.DateField(auto_now_add=True, verbose_name='Data de Início')
    end_date = models.DateField(null=True, blank=True, verbose_name='Data de Término')
    active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Assinatura'
        verbose_name_plural = 'Assinaturas'

    def __str__(self):
        status = 'Ativa' if self.active else 'Inativa'
        return f"{self.company.business_name} - {self.plan} ({status})"
