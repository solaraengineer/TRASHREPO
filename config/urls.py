from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views
from core.views import RegisterVerifyAPIView, RegisterVerifyAPIView
from core.views import LoginAPIView, LoginVerifyAPIView
from core.views import UserFetchAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('FA/', views.register2, name='FA'),
    path("dash/", views.dash, name="dashboard"),
    path('login/', views.login, name='login'),
    path('api/register/', RegisterVerifyAPIView, name='RegisterVerifyAPIView'),
    path('api/register/verify/', RegisterVerifyAPIView, name='RegisterVerifyAPI'),
    path('api/login/', LoginAPIView, name='LoginAPIView'),
    path('api/login/verify/', LoginVerifyAPIView, name='LoginVerifyAPIView'),
    path('api/user/', UserFetchAPIView, name='api-user'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)