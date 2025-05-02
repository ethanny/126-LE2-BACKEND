from rest_framework.routers import DefaultRouter
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import BookViewSet, user_books_view, register_user, GenreViewSet, all_users, UserBookStatusViewSet
from . import views
router = DefaultRouter()
router.register(r'books', BookViewSet, basename='book')
router.register(r'user/bookStatus', UserBookStatusViewSet, basename='book_status')

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', views.get_profile),
    path('register/', register_user, name='register'),
    path('user/books/', user_books_view, name='user-books'),
    path('genres/', GenreViewSet.as_view({'get': 'list'}), name='genres'),
    path('users/', all_users),
]

urlpatterns += router.urls