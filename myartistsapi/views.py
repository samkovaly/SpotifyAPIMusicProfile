
from rest_framework.views import APIView
from django.http import JsonResponse
from rest_framework.permissions import AllowAny


class Ping(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return JsonResponse({'message':  'ping successful'})