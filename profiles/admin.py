from django.contrib import admin
from .models import BookmarkedProfile
@admin.register(BookmarkedProfile)
class BookmarkedProfileAdmin(admin.ModelAdmin):
    list_display = ("username", "user", "public_repos", "followers", "created_at")
    search_fields = ("username", "name", "user__username")