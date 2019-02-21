from django.conf.urls import url

from .views import *


urlpatterns = [
    # url('', test_index),
    url('^index/$', test_index),
]
