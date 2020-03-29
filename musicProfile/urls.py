from django.contrib import admin

from django.urls import path
from django.conf.urls import include

from .spotify import get_spotify_music_profile

from musicProfile.views import UserDetail, UserProfileDetail, UserPostGetAll



urlpatterns = [
    path('users/', UserPostGetAll.as_view()),
    path('users/<str:username>', UserDetail.as_view()),
    path('users/<str:username>/music_profile', UserProfileDetail.as_view()),
]



'''
URL patterns
    auth/
        get user token
    api/users/<str:username>/
        get user by username, returns user music_profile as part of user
            must pass auth token
    api/users/<str:username>/set_music_profile/
        set users music profile
            must pass auth token
'''