from django.contrib import admin
from .models import Click

# Register your models here.

@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
    list_display = ('link', 'link__user', 'clicked_at')
    search_fields = ('link__original_url',)
    list_filter = ('clicked_at',)