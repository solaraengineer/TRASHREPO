from tkinter.font import names
from core.views import home
from django.contrib import admin
from django.urls import path
from core.views import (
    RegisterAPIView,
    RegisterVerifyAPIView,
    LoginAPIView,
    LoginVerifyAPIView,
    UserFetchAPIView,
)
urlpatterns = [
    path('', home, name='home'),
    path('api/register/', RegisterAPIView.as_view(), name='RegisterAPIView'),
    path('admin/', admin.site.urls),
    path('api/register/verify/', RegisterVerifyAPIView.as_view(), name='RegisterVerifyAPIView'),
    path('api/login/', LoginAPIView.as_view(), name='LoginAPIView'),
    path('api/login/verify/', LoginVerifyAPIView.as_view(), name='LoginVerifyAPIView'),
    path('api/user/', UserFetchAPIView.as_view(), name='UserFetchAPIView'),
]
