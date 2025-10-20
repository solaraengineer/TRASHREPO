from tkinter.font import names
from core.views import home
from django.contrib import admin
from django.urls import path
from core.views import (
    RegisterAPIView,
    LoginAPIView,
    UserFetchAPIView,
    dash,
)
urlpatterns = [
    path('', home, name='home'),
    path('api/register/', RegisterAPIView.as_view(), name='RegisterAPIView'),
    path('admin/', admin.site.urls),
    path('api/login/', LoginAPIView.as_view(), name='LoginAPIView'),
    path('api/user/', UserFetchAPIView.as_view(), name='UserFetchAPIView'),
    path('dash/', dash.as_view(), name='dash'),
]
