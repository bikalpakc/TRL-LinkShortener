from django.db import models
from django.conf import settings
import string
import random

#Generate a unique short code for the link ,appended after the main trl domain.
def generate_short_code():
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=6))
        if not Link.objects.filter(short_code=code).exists():
            return code


#Link model to store the original URL, the generated short code, and other relevant information.
class Link(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='links'
    )
    original_url = models.URLField(max_length=2000)
    short_code = models.CharField(max_length=20, unique=True, default=generate_short_code)
    custom_alias = models.CharField(max_length=50, unique=True, null=True, blank=True) #custom short code provided by the user.
    password = models.CharField(max_length=100, null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.short_code} → {self.original_url}"

    #Custom code takes precedence over the generated short code if provided by the user.
    @property
    def active_code(self):
        return self.custom_alias if self.custom_alias else self.short_code