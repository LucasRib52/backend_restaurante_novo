from django.db import models
from settings.models import Settings

# Create your models here.

class Subscription(models.Model):
    PLAN_CHOICES = [
        ('free', 'Gratuito'),
        ('basic', 'Básico'),
        ('premium', 'Premium'),
    ]
    company = models.ForeignKey(Settings, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free', verbose_name='Plano')
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
