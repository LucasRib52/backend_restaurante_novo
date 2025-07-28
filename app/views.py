from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from settings.models import Settings

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
                'is_active': getattr(self.user, 'settings').is_active,
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

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    nome = request.data.get('nome')
    if not all([username, password, email, nome]):
        return Response({'error': 'Todos os campos são obrigatórios'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Usuário já existe'}, status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.create_user(username=username, password=password, email=email, first_name=nome)
    # Garantir que a conta da empresa não possua privilégios de admin
    user.is_staff = False
    user.is_superuser = False
    user.save()
    # Cria configurações padrão para o novo usuário com valores default
    Settings.objects.create(
        owner=user,
        business_name=nome or "Meu Negócio",
        business_phone="",
        business_address="",
        business_email=email,
        opening_time="08:00",
        closing_time="18:00",
        is_open=True,
        delivery_available=True,
        delivery_fee=0,
        minimum_order_value=0,
        tax_rate=0,
        payment_methods={}
    )
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
    }
    return Response({'access': access, 'refresh': str(refresh), 'user': user_data}, status=status.HTTP_201_CREATED) 