import logging
import random
import requests
from django.shortcuts import render
from django.core.mail import send_mail
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from core.forms import RegisterForm, LoginForm
from core.models import User, FA
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, authentication_classes, permission_classes
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



@ratelimit(key='ip', rate='5/m', block=True)
class RegisterAPIView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        username = data['username']
        email = data['email']
        password = data['password']
        recaptcha_token = data['recaptcha']

        # Verify reCAPTCHA
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
        request.session['data'] = {
            'username': username,
            'email': email,
            'password': password,
            'verification_code': verification_code,
        }

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



@ratelimit(key='ip', rate='5/m', block=True)
class RegisterVerifyAPIView(APIView):
    def post(self, request):
        serializer = RegisterVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        input_code = serializer.validated_data['code']
        reg_data = request.session.get('data')
        if not reg_data:
            return Response({'error': 'Session expired.'}, status=status.HTTP_410_GONE)

        if input_code != reg_data.get("verification_code"):
            return Response({'error': 'Incorrect verification code.'}, status=status.HTTP_403_FORBIDDEN)

        if User.objects.filter(email=reg_data["email"]).exists():
            return Response({'error': 'Email already exists.'}, status=status.HTTP_409_CONFLICT)

        try:
            user = User(username=reg_data["username"], email=reg_data["email"])
            user.set_password(reg_data["password"])
            user.save()
            request.session.pop('data', None)
            return Response({'message': 'Registration complete.'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logging.error(e)
            return Response({'error': 'User creation failed.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@ratelimit(key='ip', rate='5/m', block=True)
class LoginAPIView(APIView):
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
        request.session['pending_user_id'] = user.id
        return Response({'message': '2FA code sent to email.'}, status=status.HTTP_200_OK)



@ratelimit(key='ip', rate='5/m', block=True)
class LoginVerifyAPIView(APIView):
    def post(self, request):
        serializer = LoginVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data['code']
        user_id = request.session.get('pending_user_id')
        if not user_id:
            return Response({'error': 'Session expired or no pending login.'}, status=status.HTTP_410_GONE)

        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        fa_code = FA.objects.filter(user=user).first()
        if not fa_code or fa_code.code != code:
            return Response({'error': 'Invalid 2FA code.'}, status=status.HTTP_403_FORBIDDEN)


        request.session.pop('pending_user_id', None)
        FA.objects.filter(user=user).delete()


        tokens = get_tokens_for_user(user)

        return Response({
            'message': 'Login successful.',
            'access': tokens['access'],
            'refresh': tokens['refresh']
        }, status=status.HTTP_200_OK)



@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@ratelimit(key='ip', rate='5/m', block=True)
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