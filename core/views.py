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
import inspect

from core.serializers import (
    RegisterSerializer,
    RegisterVerifySerializer,
    LoginSerializer,
    LoginVerifySerializer
)

def send_codee(user, code=None):
    if not code:
        code = str(random.randint(100000, 999999))
    FA.objects.filter(user=user).delete()
    FA.objects.create(user=user, code=code)
    try:
        send_mail(
            'Your 2FA Code',
            f'Your 2FA code is: {code}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False
        )
    except Exception as e:
        logging.error(e)
    return code

def home(request):
    return render(request, 'index.html', {
        'register_form': RegisterForm(),
        'login_form': LoginForm(),
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
    })

def fa_view(request):
    return render(request, 'FA.html')

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

        verification_code = str(random.randint(10000, 99999))

        PendingRegistration.objects.filter(email=email).delete()
        PendingRegistration.objects.create(
            username=username,
            email=email,
            password=password,
            verification_code=verification_code
        )

        try:
            send_mail(
                'Verification Code',
                f'Your Verification Code: {verification_code}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except Exception as e:
            logging.error(e)
            return Response({'error': 'Could not send verification email'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': 'Verification code sent'}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterVerifyAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        input_code = serializer.validated_data['code']
        pending = PendingRegistration.objects.filter(verification_code=input_code).first()
        if not pending:
            return Response({'error': 'Invalid or expired code'}, status=status.HTTP_403_FORBIDDEN)

        if User.objects.filter(email=pending.email).exists():
            return Response({'error': 'Email already exists.'}, status=status.HTTP_409_CONFLICT)

        try:
            user = User(username=pending.username, email=pending.email)
            user.set_password(pending.password)
            user.save()
            pending.delete()
            return Response({'message': 'Registration complete.'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logging.error(e)
            return Response({'error': 'User creation failed.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

        send_codee(user)
        FA.objects.filter(user=user).delete()
        FA.objects.create(user=user, code=send_codee(user))
        return Response({'message': '2FA code sent to email.'}, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class LoginVerifyAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data['code']
        fa = FA.objects.filter(code=code).first()
        if not fa:
            return Response({'error': 'Invalid 2FA code.'}, status=status.HTTP_403_FORBIDDEN)

        user = fa.user
        FA.objects.filter(user=user).delete()
        tokens = get_tokens_for_user(user)

        return Response({
            'message': 'Login successful.',
            'access': tokens['access'],
            'refresh': tokens['refresh']
        }, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
class UserFetchAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        return Response({
            "username": user.username,
            "email": user.email,
            "id": user.id,
            "is_staff": user.is_staff,
            "date_joined": str(user.date_joined),
        })

