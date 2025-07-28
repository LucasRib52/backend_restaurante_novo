from django.shortcuts import render
from rest_framework import generics, permissions
from .models import Subscription
from .serializers import SubscriptionSerializer

# Create your views here.

class SubscriptionListCreateView(generics.ListCreateAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

class SubscriptionRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
