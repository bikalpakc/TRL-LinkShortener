from django.db import models
from links.models import Link

class Click(models.Model):
    # This 'related_name' is what allows obj.clicks.count() to work later!
    link = models.ForeignKey(Link, on_delete=models.CASCADE, related_name='clicks')
    clicked_at = models.DateTimeField(auto_now_add=True)
    
    # Tracking data
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    country = models.CharField(max_length=100, default='Unknown')
    browser = models.CharField(max_length=200, null=True, blank=True)
    device_type = models.CharField(max_length=50, null=True, blank=True)
    referrer = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"Clicked on {self.link.short_code} at {self.clicked_at}"