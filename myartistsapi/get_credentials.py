import sys
sys.path.append("..")

from django.http import JsonResponse
from local_secrets import spotify_app_credentials_data, concert_events_API_keys


def get_spotify_app_credentials(request):
    return JsonResponse(spotify_app_credentials_data)

def get_concert_API_keys(request):
    return JsonResponse(concert_events_API_keys)