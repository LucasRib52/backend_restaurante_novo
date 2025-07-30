from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from settings.models import Settings
from assinaturas.models import Subscription

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # Apenas dados essenciais do usuário (removendo flags admin)
        data.update({
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'is_superuser': self.user.is_superuser,
                'is_staff': self.user.is_staff,
                # block flag from Settings
                'is_active': getattr(getattr(self.user, 'settings', None), 'is_active', self.user.is_active),
            }
        })
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (AllowAny,)

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_token(request):
    """
    Verifica se o token é válido
    """
    return Response({'detail': 'Token válido'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])
def check_slug_availability(request):
    """
    Verifica se um slug está disponível
    """
    slug = request.query_params.get('slug')
    if not slug:
        return Response({'error': 'Slug é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
    
    from settings.models import Settings
    from django.utils.text import slugify
    
    # Converte o slug para o formato correto
    formatted_slug = slugify(slug)
    
    # Verifica se já existe
    exists = Settings.objects.filter(business_slug=formatted_slug).exists()
    
    return Response({
        'slug': formatted_slug,
        'available': not exists,
        'message': 'Slug já está em uso' if exists else 'Slug disponível'
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        nome_restaurante = request.data.get('nome_restaurante')
        slug = request.data.get('slug')
        
        if not all([username, password, email, nome_restaurante]):
            return Response({'error': 'Todos os campos são obrigatórios'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Usuário já existe'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(username=username, password=password, email=email, first_name=nome_restaurante)
        # Garantir que a conta da empresa não possua privilégios de admin
        user.is_staff = False
        user.is_superuser = False
        user.save()
        
        # Gerar slug único
        from django.utils.text import slugify
        import random
        import string
        
        if slug:
            base_slug = slugify(slug)
        else:
            base_slug = slugify(nome_restaurante)
        
        business_slug = base_slug
        
        # Se o slug já existe, gerar um aleatório
        if Settings.objects.filter(business_slug=business_slug).exists():
            # Gerar string aleatória de 6 caracteres
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            business_slug = f"{base_slug}-{random_suffix}"
        
        # Cria configurações padrão para o novo usuário com valores default
        settings_obj = Settings.objects.create(
            owner=user,
            business_name=nome_restaurante,
            business_slug=business_slug,
            business_phone="",
            business_address="",
            business_email=email,
            opening_time="08:00",
            closing_time="18:00",
            is_open=True,
            is_active=True,
            delivery_available=True,
            delivery_fee=0,
            minimum_order_value=0,
            tax_rate=0,
            payment_methods={}
        )
        
        from datetime import date, timedelta
        Subscription.objects.create(
            company=settings_obj,
            plan='free',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            active=True
        )
        
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'is_active': settings_obj.is_active,
        }
        return Response({'access': access, 'refresh': str(refresh), 'user': user_data}, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"Erro no registro: {str(e)}")
        return Response({'error': f'Erro interno do servidor: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 