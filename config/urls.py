from django.urls import path
from core import views

urlpatterns = [
    path('api/register/', views.RegisterAPIView.as_view(), name='RegisterAPIView'),
    path('api/register/verify/', views.RegisterVerifyAPIView.as_view(), name='RegisterVerifyAPIView'),
    path('api/login/', views.LoginAPIView.as_view(), name='LoginAPIView'),
    path('api/login/verify/', views.LoginVerifyAPIView.as_view(), name='LoginVerifyAPIView'),
    path('api/user/', views.UserFetchAPIView.as_view(), name='UserFetchAPIView'),
]