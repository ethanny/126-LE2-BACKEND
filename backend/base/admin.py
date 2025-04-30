from django.contrib import admin
from .models import Profile, Genre, Book, Review, Comment, UserBookStatus

admin.site.register(Profile)

# Register models in Django Admin
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'average_rating', 'contributor')
    search_fields = ('title', 'author')
    list_filter = ('genres',)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'rating', 'created_at')
    search_fields = ('book__title', 'user__username')
    list_filter = ('book', 'user')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'review', 'created_at')
    search_fields = ('review__book__title', 'user__username')

class UserBookStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'status')
    search_fields = ('user__username', 'book__title')
    list_filter = ('status',)

# Register the models with custom admin views
admin.site.register(Genre, GenreAdmin)
admin.site.register(Book, BookAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(UserBookStatus, UserBookStatusAdmin)