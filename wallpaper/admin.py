from django.contrib import admin

from django.contrib import admin

from .models import (
    Wallpaper
)


@admin.register(Wallpaper)
class LanguageAdmin(admin.ModelAdmin):
    fields = [
        "name", "original_url", "mp3",
    ]
    list_display = (
        "id", "name", "original_url", "mp3",
    )
    list_per_page = 50
    ordering = ('id',)
    list_editable = [
        "name", "original_url", "mp3"
    ]
