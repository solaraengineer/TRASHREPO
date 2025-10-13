from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views
from views import api_register, api_register_verify
from views import api_login, api_login_verify

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('FA/', views.register2, name='FA'),
    path("dash/", views.dash, name="dashboard"),
    path('login/', views.login, name='login'),
    path('api/register/', api_register, name='api-register'),
    path('api/register/verify/', api_register_verify, name='api-register-verify'),
    path('api/login/', api_login, name='api-login'),
    path('api/login/verify/', api_login_verify, name='api-login-verify'),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)