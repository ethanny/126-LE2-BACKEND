from rest_framework.routers import DefaultRouter
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import BookViewSet, user_books_view, register_user, GenreViewSet, all_users, UserBookStatusViewSet
from . import views
from rest_framework_nested import routers

router = DefaultRouter()
router.register(r'books', BookViewSet, basename='book')
router.register(r'user/bookStatus', UserBookStatusViewSet, basename='book_status')

books_router = routers.NestedDefaultRouter(router, r'books', lookup='book')
books_router.register(r'reviews', views.ReviewViewSet, basename='book-reviews')

reviews_router = routers.NestedDefaultRouter(books_router, r'reviews', lookup='review')
reviews_router.register(r'comments', views.CommentViewSet, basename='review-comments')

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', views.get_profile),
    path('register/', register_user, name='register'),
    path('user/books/', user_books_view, name='user-books'),
    path('genres/', GenreViewSet.as_view({'get': 'list'}), name='genres'),
    path('users/', all_users),
    path('', include(router.urls)),
    path('', include(books_router.urls)),
    path('', include(reviews_router.urls)),
]

urlpatterns += router.urls