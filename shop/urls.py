from django.conf.urls import url
from .views import (poloznica)

urlpatterns = [
    url(r'^poloznica/', poloznica),]