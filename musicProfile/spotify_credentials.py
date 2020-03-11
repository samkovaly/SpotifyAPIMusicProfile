import sys
sys.path.append("..")

from django.http import JsonResponse
from local_secrets import spotify_app_credentials_data


def get_spotify_app_credentials(request):
    return JsonResponse(spotify_app_credentials_data)