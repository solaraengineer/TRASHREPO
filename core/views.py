import logging
import random
import requests
from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from core.forms import RegisterForm, LoginForm
from core.models import PendingRegistration, User, FA
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import  authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.views import View
import inspect

from core.serializers import (
    RegisterSerializer,
    RegisterVerifySerializer,
    LoginSerializer,
    LoginVerifySerializer
)


def home(request):
    return render(request, 'index.html', {
        'register_form': RegisterForm(),
        'login_form': LoginForm(),
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
    })
class fa_view(View):
    def get(self, request):
       return render(request, 'fa.html', {})

class dash(View):
    def get(self, request):
        return render(request, 'dash.html')

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@method_decorator(csrf_exempt, name='dispatch')
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        username = data['username']
        email = data['email']
        password = data['password']
        recaptcha_token = data['recaptcha']

        verify_url = "https://www.google.com/recaptcha/api/siteverify"
        payload = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_token,
        }
        try:
            res = requests.post(verify_url, data=payload, timeout=5)
            recaptcha_data = res.json()
        except requests.RequestException:
            return Response({'error': 'reCAPTCHA error'}, status=status.HTTP_400_BAD_REQUEST)

        if not recaptcha_data.get('success'):
            return Response({'error': 'Invalid reCAPTCHA'}, status=status.HTTP_403_FORBIDDEN)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already registered'}, status=status.HTTP_409_CONFLICT)

        user = User(email=email, username=username)
        user.set_password(password)
        user.save()

        return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)

@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = User.objects.filter(email=email).first()
        if not user or not user.check_password(password):
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        tokens = get_tokens_for_user(user)
        return Response(tokens, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
class UserFetchAPIView(APIView):

    def get(self, request):
        user = request.user
        return Response({
            "username": user.username,
            "email": user.email,
            "id": user.id,
            "is_staff": user.is_staff,
            "date_joined": str(user.date_joined),
        })
