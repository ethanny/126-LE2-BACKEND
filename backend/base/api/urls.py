from django.urls import path
from . import views
from .views import MyTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from .views import register_user

urlpatterns = [
   path('', views.get_routes),
   path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
   path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
   path('profile/', views.get_profile),
   path('register/', register_user, name='register'),
]