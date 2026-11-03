from django.contrib.auth.models import User
from django.db import models


class BookmarkedProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
    username = models.CharField(max_length=39)          # GitHub username
    name = models.CharField(max_length=150, blank=True)
    avatar_url = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    public_repos = models.PositiveIntegerField(default=0)
    followers = models.PositiveIntegerField(default=0)
    html_url = models.URLField(blank=True)
    note = models.TextField(blank=True, default="")      # Bonus: personal notes
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "username")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.username} (saved by {self.user})"
