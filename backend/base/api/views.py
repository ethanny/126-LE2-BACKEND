from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
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
from collections import Counter
from django.db.models import Count, Q, Avg

@api_view(['GET'])
def get_routes(request):
    """returns a view containing all the possible routes"""
    routes = [
        '/api/token',
        '/api/token/refresh'
    ]

    return Response(routes)


@api_view(['GET'])
@permission_classes([AllowAny])
def all_users(request):
    # Get all users with their basic info
    users = User.objects.all().values('id', 'username')
    
    # Convert QuerySet to list to allow modification
    users_list = list(users)
    
    # Add review count for each user
    for user_data in users_list:
        review_count = Review.objects.filter(user_id=user_data['id']).count()
        user_data['review_count'] = review_count
    
    return Response(users_list)

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
def user_books_view(request):
    contributed = Book.objects.filter(contributor=request.user)
    read = Book.objects.filter(user_statuses__user=request.user, user_statuses__status='read')
    reading = Book.objects.filter(user_statuses__user=request.user, user_statuses__status='reading')
    want = Book.objects.filter(user_statuses__user=request.user, user_statuses__status='want')

    recommendations = get_recommendations_by_genre(request.user)

    return Response({
        'contributed': BookSerializer(contributed, many=True).data,
        'read': BookSerializer(read, many=True).data,
        'reading': BookSerializer(reading, many=True).data,
        'want': BookSerializer(want, many=True).data,
        'recommendations': BookSerializer(recommendations, many=True).data,
    })

def get_recommendations_by_genre(user):
    """
    Generate book recommendations based on the genres of books in the user's shelves.
    
    Algorithm:
    1. Identify the most common genres in the user's read and reading shelves
    2. Find popular books in those genres that the user hasn't interacted with yet
    3. Return a curated list of recommendations based on ratings and genre relevance
    
    Args:
        user: The user object for whom to generate recommendations
        
    Returns:
        QuerySet of Book objects recommended for the user
    """
    # Get all books the user has interacted with
    user_books = Book.objects.filter(
        user_statuses__user=user
    ).values_list('id', flat=True)
    
    # Get the genres from user's read and reading books
    user_genres = Book.objects.filter(
        user_statuses__user=user,
        user_statuses__status__in=['read', 'reading']
    ).values_list('genres__id', flat=True).distinct()
    
    # Remove None values if any exist
    user_genres = [genre_id for genre_id in user_genres if genre_id is not None]
    
    # Count genre occurrences and get the top 3
    genre_counter = Counter(user_genres)
    top_genres = [genre_id for genre_id, _ in genre_counter.most_common(3)]
    
    if not top_genres:
        # Fallback to popular books if no genres are found
        return Book.objects.exclude(id__in=user_books).order_by('-reviews__rating')[:10]
    
    # Get recommendations based on top genres, excluding books the user already has
    recommendations = Book.objects.filter(
        genres__id__in=top_genres
    ).exclude(
        id__in=user_books
    ).annotate(
        relevance=Count('genres', filter=Q(genres__id__in=top_genres)),
        avg_rating=Avg('reviews__rating')
    ).order_by(
        '-avg_rating', '-relevance'
    ).distinct()[:10]
    
    return recommendations

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


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]


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

    @action(detail=False, methods=['delete'])
    def remove(self, request):
        book_id = request.query_params.get('book', None)
        if not book_id:
            return Response({"error": "Book ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            status_obj = UserBookStatus.objects.get(user=request.user, book_id=book_id)
            status_obj.delete()
            return Response({"message": "Book removed from shelf"}, status=status.HTTP_204_NO_CONTENT)
        except UserBookStatus.DoesNotExist:
            return Response({"error": "Book status not found"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], url_path='status')
    def get_book_status(self, request):
        book_id = request.query_params.get('book')
        if not book_id:
            return Response({"error": "Book ID is required"}, status=400)

        try:
            status_obj = UserBookStatus.objects.get(user=request.user, book_id=book_id)
            return Response({"status": status_obj.status})
        except UserBookStatus.DoesNotExist:
            return Response({"status": None})