from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from .models import Settings, OpeningHour
from .serializers import SettingsSerializer, OpeningHourSerializer
import json
from datetime import datetime

# Create your views here.

class SettingsDetailView(generics.RetrieveUpdateAPIView):
    """
    API para recuperar e atualizar as configurações do sistema.
    """
    serializer_class = SettingsSerializer

    def get_object(self):
        # Busca ou cria as configurações para o usuário autenticado
        obj, created = Settings.objects.get_or_create(
            owner=self.request.user,
            defaults={
                "business_name": "Meu Negócio",
                "business_phone": "",
                "business_address": "",
                "business_email": "",
                "opening_time": "08:00",
                "closing_time": "18:00",
                "is_open": True,
                "delivery_available": True,
                "delivery_fee": 0,
                "minimum_order_value": 0,
                "tax_rate": 0,
            }
        )
        return obj

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data.copy()
            
            # Remove opening_hours dos dados se existir
            opening_hours_data = data.pop('opening_hours', None)
            
            # Atualiza as configurações básicas
            serializer = self.get_serializer(instance, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            # Atualiza os horários de funcionamento
            if opening_hours_data:
                try:
                    # Se vier como string (por multipart), faz o parse
                    if isinstance(opening_hours_data, str):
                        # Remove colchetes extras se existirem
                        if opening_hours_data.startswith('[') and opening_hours_data.endswith(']'):
                            opening_hours_data = opening_hours_data[1:-1]
                        opening_hours_data = json.loads(opening_hours_data)
                    
                    # Se for uma lista com um único item string, faz parse novamente
                    if isinstance(opening_hours_data, list) and len(opening_hours_data) == 1 and isinstance(opening_hours_data[0], str):
                        opening_hours_data = json.loads(opening_hours_data[0])
                    
                    # Remove horários existentes
                    instance.opening_hours.all().delete()
                    
                    # Cria novos horários
                    for oh_data in opening_hours_data:
                        # Garante que os dados estão no formato correto
                        day_of_week = int(oh_data.get('day_of_week', 0))
                        opening_time = str(oh_data.get('opening_time', '08:00'))
                        closing_time = str(oh_data.get('closing_time', '18:00'))
                        is_open = bool(oh_data.get('is_open', True))
                        is_holiday = bool(oh_data.get('is_holiday', False))
                        
                        # Cria o horário de funcionamento
                        opening_hour = OpeningHour.objects.create(
                            settings=instance,
                            day_of_week=day_of_week,
                            opening_time=opening_time,
                            closing_time=closing_time,
                            is_open=is_open,
                            is_holiday=is_holiday
                        )
                        
                        # Chama o método clean para definir next_day_closing
                        opening_hour.clean()
                        opening_hour.save()

                except Exception as e:
                    print(f"Erro ao processar horários: {str(e)}")
                    print(f"Dados recebidos: {opening_hours_data}")
                    return Response(
                        {"opening_hours": str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Retorna os dados atualizados
            return Response(self.get_serializer(instance).data)
            
        except Exception as e:
            print(f"Erro geral: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
