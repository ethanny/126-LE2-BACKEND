from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username

class Genre(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    synopsis = models.TextField()
    genres = models.ManyToManyField(Genre, related_name='books')
    cover_url = models.URLField(blank=True)
    contributor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contributed_books')

    def __str__(self):
        return self.title

    @property
    def review_count(self):
        return self.reviews.count()

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return sum([r.rating for r in reviews]) / reviews.count()
        return 0

class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=100, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.rating})"

class Comment(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('review', 'user')  # user can only comment once per review

    def __str__(self):
        return f"{self.user.username} on {self.review}"

class UserBookStatus(models.Model):
    STATUS_CHOICES = [
        ('read', 'Read'),
        ('reading', 'Currently Reading'),
        ('want', 'Want to Read'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_statuses')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='user_statuses')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.status})"
    
