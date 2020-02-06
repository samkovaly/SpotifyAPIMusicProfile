from django.contrib import admin
from django.urls import path

from django.conf.urls import include
from rest_framework import routers

from .spotify_credentials import get_spotify_app_credentials
from .spotify import get_spotify_music_profile


urlpatterns = [
    path('spotify-app-credentials/', get_spotify_app_credentials),
    path('spotify-music-profile/', get_spotify_music_profile),
]
