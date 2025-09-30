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

# Home page
def home(request):
    return render(request, 'index.html', {
        'register_form': RegisterForm(),
        'login_form': LoginForm(),
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
        'recaptcha_secret_key': settings.RECAPTCHA_SECRET_KEY,
    })


# Register view
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