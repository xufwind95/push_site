from django.conf.urls import url

from .views import get_wallpaper


urlpatterns = [
    # url('', test_index),
    url('^wallpaper_upload/$', get_wallpaper),
]
