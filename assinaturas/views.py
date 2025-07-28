from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Subscription, Plan
from .serializers import SubscriptionSerializer, PlanSerializer
import logging

logger = logging.getLogger(__name__)

# Create your views here.

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def debug_subscriptions(request):
    """
    View de debug para verificar as assinaturas do usuário
    """
    user = request.user
    settings = getattr(user, 'settings', None)
    
    debug_info = {
        'user_id': user.id,
        'username': user.username,
        'has_settings': settings is not None,
        'settings_id': settings.id if settings else None,
        'settings_name': settings.business_name if settings else None,
        'total_subscriptions': 0,
        'subscriptions': [],
        'all_subscriptions_count': Subscription.objects.count(),
        'all_subscriptions': list(Subscription.objects.values('id', 'company__business_name', 'plan', 'start_date', 'end_date', 'active'))
    }
    
    if settings:
        subscriptions = Subscription.objects.filter(company=settings)
        debug_info['total_subscriptions'] = subscriptions.count()
        debug_info['subscriptions'] = list(subscriptions.values('id', 'plan', 'start_date', 'end_date', 'active'))
    
    logger.info(f"Debug subscriptions: {debug_info}")
    return Response(debug_info)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_test_subscription(request):
    """
    Cria uma assinatura de teste para debug
    """
    user = request.user
    settings = getattr(user, 'settings', None)
    
    if not settings:
        return Response({'error': 'Usuário não possui settings'}, status=400)
    
    try:
        from datetime import date, timedelta
        
        # Criar uma assinatura de teste
        subscription = Subscription.objects.create(
            company=settings,
            plan='Teste',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            active=True
        )
        
        return Response({
            'success': True,
            'subscription_id': subscription.id,
            'message': 'Assinatura de teste criada com sucesso'
        })
    except Exception as e:
        logger.error(f"Erro ao criar assinatura de teste: {e}")
        return Response({'error': str(e)}, status=500)

class SubscriptionListCreateView(generics.ListCreateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retorna as assinaturas apenas da empresa (Settings) vinculada ao usuário logado,
        ordenadas da mais recente para a mais antiga.
        """
        user = self.request.user
        settings = getattr(user, 'settings', None)
        
        logger.info(f"Usuário: {user.username}, Settings: {settings}")
        
        if not settings:
            logger.warning(f"Usuário {user.username} não possui settings")
            return Subscription.objects.none()
        
        subscriptions = Subscription.objects.filter(company=settings).order_by('-start_date')
        logger.info(f"Encontradas {subscriptions.count()} assinaturas para empresa {settings.business_name}")
        
        # Log detalhado das assinaturas encontradas
        for sub in subscriptions:
            logger.info(f"Assinatura: ID={sub.id}, Plano={sub.plan}, Ativa={sub.active}, Início={sub.start_date}, Fim={sub.end_date}")
        
        return subscriptions

    def list(self, request, *args, **kwargs):
        """
        Sobrescreve o método list para adicionar logs
        """
        logger.info(f"Listando assinaturas para usuário: {request.user.username}")
        queryset = self.get_queryset()
        logger.info(f"Queryset retornou {queryset.count()} assinaturas")
        
        serializer = self.get_serializer(queryset, many=True)
        logger.info(f"Serializer retornou {len(serializer.data)} itens")
        
        return Response(serializer.data)

    def perform_create(self, serializer):
        """
        Cria uma nova assinatura para a empresa logada.
        - Encerra a assinatura ativa (se existir)
        - Define a data de término padrão (30 dias) para planos pagos
        """
        user = self.request.user
        settings = getattr(user, 'settings', None)
        if not settings:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Usuário não possui empresa associada.')

        # Tornar qualquer assinatura ativa anterior como inativa
        Subscription.objects.filter(company=settings, active=True).update(active=False)

        # Determinar data de término para planos pagos com base na duração do plano
        plan_code = self.request.data.get('plan', 'free')
        end_date = None
        if plan_code != 'free':
            from datetime import date, timedelta
            plan_obj = Plan.objects.filter(name__iexact=plan_code).first()
            duration = plan_obj.duration_days if plan_obj else 30
            end_date = date.today() + timedelta(days=duration)

        serializer.save(company=settings, plan=plan_code, end_date=end_date, active=True)

class SubscriptionRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]


# View to get the current user's active subscription
class CurrentSubscriptionView(generics.RetrieveAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        settings = getattr(user, 'settings', None)
        if not settings:
            # If user has no company settings, raise 404
            from rest_framework.exceptions import NotFound
            raise NotFound('Configurações da empresa não encontradas para o usuário.')

        subscription = (
            Subscription.objects.filter(company=settings, active=True)
            .order_by('-end_date')
            .first()
        )

        if not subscription:
            from rest_framework.exceptions import NotFound
            raise NotFound('Assinatura ativa não encontrada.')

        return subscription


class PlanListCreateView(generics.ListCreateAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def get_permissions(self):
        # Allow anyone authenticated to list; only admin can create
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]
