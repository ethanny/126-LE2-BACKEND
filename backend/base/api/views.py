from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .serializer import MyTokenObtainPairSerializer, ProfileSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from base.models import Profile, Book, Review, Comment, Genre, UserBookStatus
from rest_framework import status, viewsets, permissions
from .serializer import (
    BookSerializer, BookCreateSerializer,
    ReviewSerializer, CommentSerializer,
    GenreSerializer, UserBookStatusSerializer
)
from django.shortcuts import get_object_or_404

@api_view(['GET'])
def get_routes(request):
    """returns a view containing all the possible routes"""
    routes = [
        '/api/token',
        '/api/token/refresh'
    ]

    return Response(routes)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    user = request.user
    profile = user.profile
    serializer = ProfileSerializer(profile, many=False)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    full_name = request.data.get('full_name')

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password)
    Profile.objects.create(user=user, full_name=full_name)

    return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_books_view(request):
    contributed = Book.objects.filter(contributor=request.user)
    read = Book.objects.filter(user_statuses__user=request.user, user_statuses__status='read')
    reading = Book.objects.filter(user_statuses__user=request.user, user_statuses__status='reading')

    return Response({
        'contributed': BookSerializer(contributed, many=True).data,
        'read': BookSerializer(read, many=True).data,
        'reading': BookSerializer(reading, many=True).data,
    })

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# --- Book ViewSet ---
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BookCreateSerializer
        return BookSerializer

    def perform_create(self, serializer):
        serializer.save(contributor=self.request.user)


# --- Review ViewSet ---
class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Review.objects.filter(book__id=self.kwargs['book_pk'])

    def perform_create(self, serializer):
        book = get_object_or_404(Book, pk=self.kwargs['book_pk'])
        # Allow only one review per user per book
        if Review.objects.filter(user=self.request.user, book=book).exists():
            raise serializer.ValidationError("You have already reviewed this book.")
        serializer.save(user=self.request.user, book=book)

    def destroy(self, request, *args, **kwargs):
        review = self.get_object()
        if review.user != request.user:
            return Response({'detail': 'Not allowed to delete others reviews.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


# --- Comment ViewSet ---
class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(review__id=self.kwargs['review_pk'])

    def perform_create(self, serializer):
        review = get_object_or_404(Review, pk=self.kwargs['review_pk'])
        # Only allow one comment per user per review
        if Comment.objects.filter(user=self.request.user, review=review).exists():
            raise serializer.ValidationError("You have already commented on this review.")
        serializer.save(user=self.request.user, review=review)


# --- Genre ViewSet (Read-Only) ---
class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


# --- UserBookStatus ViewSet ---
class UserBookStatusViewSet(viewsets.ModelViewSet):
    serializer_class = UserBookStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserBookStatus.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Update or create to allow changing status
        status_obj, created = UserBookStatus.objects.update_or_create(
            user=self.request.user,
            book=serializer.validated_data['book'],
            defaults={"status": serializer.validated_data['status']}
        )
        return status_obj