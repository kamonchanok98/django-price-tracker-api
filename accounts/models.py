from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    line_user_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text="LINE User ID obtained via LINE Login",
    )
    picture_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.line_user_id}"
