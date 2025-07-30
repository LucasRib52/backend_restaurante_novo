from django.db import models
from django.utils.text import slugify
from django.db.models import JSONField
from django.core.exceptions import ValidationError
from django.utils import timezone
import pytz
from datetime import datetime, time
from django.contrib.auth.models import User  # import para multi-tenancy

class OpeningHour(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Segunda'),
        (1, 'Terça'),
        (2, 'Quarta'),
        (3, 'Quinta'),
        (4, 'Sexta'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    settings = models.ForeignKey('Settings', on_delete=models.CASCADE, related_name='opening_hours')
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_open = models.BooleanField(default=True)
    is_holiday = models.BooleanField(default=False)
    next_day_closing = models.BooleanField(default=False, help_text='Indica se o fechamento é no dia seguinte')

    class Meta:
        unique_together = ('settings', 'day_of_week', 'is_holiday')
        verbose_name = 'Horário de Funcionamento'
        verbose_name_plural = 'Horários de Funcionamento'

    def __str__(self):
        return f"{self.get_day_of_week_display()} - {'Feriado' if self.is_holiday else 'Normal'}"

    def clean(self):
        if self.opening_time and self.closing_time:
            # Se o horário de fechamento for menor que o de abertura, 
            # automaticamente marca como fechamento no dia seguinte
            if self.closing_time < self.opening_time:
                self.next_day_closing = True

    def is_currently_open(self):
        """
        Verifica se o restaurante está aberto no momento atual
        """
        now = timezone.now().astimezone(pytz.timezone('America/Sao_Paulo'))
        current_time = now.time()
        current_day = now.weekday()

        if not self.is_open:
            return False

        # Se o fechamento é no dia seguinte
        if self.next_day_closing:
            # Se estamos no dia da abertura
            if current_day == self.day_of_week:
                # Se já passou do horário de abertura
                return current_time >= self.opening_time
            # Se estamos no dia do fechamento
            elif current_day == (self.day_of_week + 1) % 7:
                # Se ainda não passou do horário de fechamento
                return current_time <= self.closing_time
            # Se estamos em um dia entre a abertura e o fechamento (para casos de múltiplos dias)
            elif self.day_of_week > current_day:
                # Se o dia de abertura é depois do dia atual (ex: domingo > segunda)
                # significa que o período começou no dia anterior
                return True
            return False
        else:
            # Se o fechamento é no mesmo dia
            if current_day == self.day_of_week:
                return self.opening_time <= current_time <= self.closing_time
            return False

class Settings(models.Model):
    """
    Modelo que representa as configurações do sistema.
    """
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')  # separação por empresa
    business_name = models.CharField(max_length=100, verbose_name='Nome do Negócio')
    business_phone = models.CharField(max_length=20, verbose_name='Telefone')
    business_address = models.CharField(max_length=200, verbose_name='Endereço')
    business_email = models.EmailField(verbose_name='E-mail')
    business_photo = models.ImageField(upload_to='restaurant_photos/', null=True, blank=True, verbose_name='Foto do Restaurante')
    business_slug = models.SlugField(max_length=100, unique=True, null=True, blank=True, verbose_name='Link Personalizado')
    opening_time = models.TimeField(verbose_name='Horário de Abertura')
    closing_time = models.TimeField(verbose_name='Horário de Fechamento')
    is_open = models.BooleanField(default=True, verbose_name='Aberto')
    delivery_available = models.BooleanField(default=True, verbose_name='Delivery Disponível')
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Taxa de Entrega')
    minimum_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Pedido Mínimo')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Taxa de Imposto (%)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_methods = JSONField(default=dict, blank=True, null=True, verbose_name='Formas de Pagamento')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Configuração'
        verbose_name_plural = 'Configurações'

    def __str__(self):
        return self.business_name

    def save(self, *args, **kwargs):
        if not self.business_slug and self.business_name:
            self.business_slug = slugify(self.business_name)
        
        # Verificar se o business_slug já existe (exceto para este próprio objeto)
        if self.business_slug:
            existing = Settings.objects.filter(business_slug=self.business_slug).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(f'Já existe um negócio com o slug "{self.business_slug}". Escolha outro nome.')
        
        super().save(*args, **kwargs)

    def is_open_now(self):
        now = timezone.now().astimezone(pytz.timezone('America/Sao_Paulo'))
        weekday = now.weekday()
        time_now = now.time()

        for oh in self.opening_hours.filter(is_open=True):
            day = oh.day_of_week
            open_time = oh.opening_time
            close_time = oh.closing_time

            if oh.next_day_closing:
                # Se hoje é o dia da abertura e já passou da abertura
                if weekday == day and time_now >= open_time:
                    return True
                # Se hoje é o dia do fechamento e ainda não passou do fechamento
                if weekday == (day + 1) % 7 and time_now <= close_time:
                    return True
                # Se estamos em um dia entre a abertura e o fechamento (para casos de múltiplos dias)
                if day > weekday:
                    # Se o dia de abertura é depois do dia atual (ex: domingo > segunda)
                    # significa que o período começou no dia anterior
                    return True
            else:
                if weekday == day and open_time <= time_now <= close_time:
                    return True
        return False
