import logging
import random
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django_ratelimit.decorators import ratelimit
from core.forms import RegisterForm, LoginForm
from core.models import User, FA
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import login as auth_login
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
        'recaptcha_secret_key': settings.RECAPTCHA_SECRET_KEY,
    })


@ratelimit(key='ip', rate='5/m', block=True)
def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = User.objects.filter(email=email).first()

            if user and user.check_password(password):
                code = send_codee(user)
                messages.info(request, "2FA code sent to your email.")
                return render(request, "FA.html", {})
            else:
                messages.error(request, "Invalid login credentials.")
                return render(request, "index.html", {
        'register_form': RegisterForm(),
        'login_form': LoginForm(),
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
         })

@ratelimit(key='ip', rate='5/m', block=True)
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            recaptcha_token = request.POST.get('g-recaptcha-response')
            verify_url = "https://www.google.com/recaptcha/api/siteverify"
            payload = {
                'secret': settings.RECAPTCHA_SECRET_KEY,
                'response': recaptcha_token,
            }

            try:
                res = requests.post(verify_url, data=payload, timeout=5)
                data = res.json()
            except requests.RequestException:
                messages.error(request, "Error verifying reCAPTCHA. Please try again.")
                return render(request, "index.html", {
                    "register_form": form,
                    "login_form": LoginForm(),
                    "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
                })

            if not data.get('success'):
                messages.error(request, "reCAPTCHA failed. Please try again.")
                return render(request, "index.html", {
                    "register_form": form,
                    "login_form": LoginForm(),
                    "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
                })

            verification_code = str(random.randint(10000, 99999))

            request.session['data'] = {
                'username': cd["username"],
                'email': cd["email"],
                'password': cd["password"],
                'verification_code': verification_code,
            }

            send_mail(
                'Verification Code',
                f'Your Verification Code: {verification_code}',
                settings.DEFAULT_FROM_EMAIL,
                [cd["email"]],
                fail_silently=False,
            )

            return redirect("/FA")
        else:
            messages.error(request, "Form is invalid. Please check your data.")

            return render(request, "index.html", {
                "register_form": form,
                "login_form": LoginForm(),
                "recaptcha_site_key": settings.RECAPTCHA_SITE_KEY,
            })

def register2(request):
    reg_data = request.session.get('data')
    if not reg_data:
        messages.error(request, "Session expired. Try registering again.")
        return redirect("/")
    if request.method == 'POST':
        input_code = request.POST.get('code', '').strip()
        correct_code = reg_data.get("verification_code")

        if input_code == correct_code:
            try:
                if User.objects.filter(email=reg_data["email"]).exists():
                    messages.error(request, "Email already exists.")
                    return redirect("/")
                user = User(
                    username=reg_data["username"],
                    email=reg_data["email"],
                )
                user.set_password(reg_data["password"])
                user.save()
                request.session.pop('data', None)
                messages.success(request, "Registration complete. Welcome!")
                return redirect("/dash")

            except Exception as e:
                print("User creation error:", e)
                messages.error(request, "Something went wrong. Try again.")
                return redirect("/")
        else:
            messages.error(request, "Invalid 2FA code.")

    return render(request, "FA.html")


@login_required
def dash(request):
    return render(request, 'dash.html')

def fa_view(request):
    return render(request, 'FA.html')


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
            user = User(
                username=reg_data["username"],
                email=reg_data["email"],
            )
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

        auth_login(request, user)
        request.session.pop('pending_user_id', None)
        FA.objects.filter(user=user).delete()

        return Response({'message': 'Login successful.'}, status=status.HTTP_200_OK)