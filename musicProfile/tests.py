
from rest_framework.test import APITestCase
from rest_framework.test import APIClient

from django.contrib.auth.models import User
from .models import UserProfile
from rest_framework.authtoken.models import Token
from rest_framework import status

import json

#from musicProfile.spotify_auth_functionality import get_access_token

import sys
sys.path.append("..")
from local_secrets import spotify_app_credentials
from local_secrets import SECRET_APP_KEY



API_URL = '/api/'
LOGIN_URL = API_URL+'login/'
REGISTER_URL = API_URL+'register/'

USERS_URL = API_URL+'users/'
MUSIC_PROFILE_URL= USERS_URL + 'music_profile/'


# must be fresh, probably provided by yourself via your own app or the spotify
TESTING_USERNAME = 'axaviar'
TESTING_REFRESH_TOKEN = 'AQAtpRiO2S0mr76W2Agn1o_3TVEvw5Ylz23-uTf60bqx2NVvEFcpkhmEfBvct94da_WRNj36REjIs0BKRgGvK4KUwPQCrrkZJTgQTYN4o9VPH5tzGGQ3hig3iM20XWbQNMA'
TESTING_ACCESS_TOKEN = 'BQDw0aNyKcdRqGfEWzXz9A4FJMcLg3kvA5hrrMUUjsSXyIPk6qFfyQ7QoHVp75EFWSllH4EGi4YvHgLxILaj9a7BL6JAGj4Lr8ov1tIvlL973w3Ef7gAf7Tf8sjbJ86BfH1f_hz7v2aaWzCXZg1KgOG6piRyBC5GDV4s7vJu6oRHrFAQDq0fJQXXm3Y2bJEEktao7-ThkFnCnw3kUyBytY1-TRFBpd6I50Qsmi9aVes2BF-09YsMAgY8vHnk'

class TestUsers(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
    def test_register_without_all_fields(self):
        response = self.client.post(REGISTER_URL, {'username': TESTING_USERNAME, 'refresh_token': TESTING_REFRESH_TOKEN})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        response = self.client.post(REGISTER_URL, {'username': TESTING_USERNAME, 'access_token': TESTING_ACCESS_TOKEN})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        response = self.client.post(REGISTER_URL, {'access_token': TESTING_ACCESS_TOKEN, 'refresh_token': TESTING_REFRESH_TOKEN})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_register_access_token_username_mismatch(self):
        response = self.client.post(REGISTER_URL, {'username': 'random_lol', 'access_token': TESTING_ACCESS_TOKEN, 'refresh_token': TESTING_REFRESH_TOKEN})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_register_new_user(self):
        response = self.client.post(REGISTER_URL, {'username': TESTING_USERNAME, 'access_token': TESTING_ACCESS_TOKEN, 'refresh_token': TESTING_REFRESH_TOKEN})
        assert response.status_code == status.HTTP_201_CREATED


    def test_register_old_user(self):
        response = self.client.post(REGISTER_URL, {'username': TESTING_USERNAME, 'access_token': TESTING_ACCESS_TOKEN, 'refresh_token': TESTING_REFRESH_TOKEN})
        
        response = self.client.post(REGISTER_URL, {'username': TESTING_USERNAME, 'access_token': TESTING_ACCESS_TOKEN, 'refresh_token': 'new_refreshnew_refresh_tokennew_refresh_tokennew_refresh_tokennew_refresh_token_tokennew_refresh_token'})
        assert response.status_code == status.HTTP_201_CREATED

    # get user auth token for user0 and make sure it works
    # aka: user login
    def test_login_auth_token(self):
        response = self.client.post(REGISTER_URL, {'username': TESTING_USERNAME, 'access_token': TESTING_ACCESS_TOKEN, 'refresh_token': TESTING_REFRESH_TOKEN})

        response = self.client.post(LOGIN_URL, {'username': TESTING_USERNAME, 'refresh_token': TESTING_REFRESH_TOKEN})
        assert response.status_code == status.HTTP_200_OK

        token = response.data['token']
        assert token is not None

    def test_login_bad_credentials(self):
        response = self.client.post(REGISTER_URL, {'username': TESTING_USERNAME, 'access_token': TESTING_ACCESS_TOKEN, 'refresh_token': TESTING_REFRESH_TOKEN})

        response = self.client.post(LOGIN_URL, {'username': TESTING_USERNAME, 'refresh_token': 'blah'})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_login_no_refresh_token(self):
        response = self.client.post(REGISTER_URL, {'username': TESTING_USERNAME, 'access_token': TESTING_ACCESS_TOKEN, 'refresh_token': TESTING_REFRESH_TOKEN})

        response = self.client.post(LOGIN_URL, {'username': TESTING_USERNAME})
        assert response.status_code == status.HTTP_400_BAD_REQUEST



class TestUserMusicProfiles(APITestCase):
    def setUp(self):
        self.client = APIClient()
    
        self.user0 = User.objects.create_user(username='mike', password='pass')
        self.user0_token = Token.objects.create(user=self.user0)

        self.register_response = self.client.post(REGISTER_URL, {'username': TESTING_USERNAME, 'access_token': TESTING_ACCESS_TOKEN, 'refresh_token': TESTING_REFRESH_TOKEN})
        

    def test_get_user_with_user_permission(self):
        response = self.client.post(LOGIN_URL, {'username': TESTING_USERNAME, 'refresh_token': TESTING_REFRESH_TOKEN})
        token = response.data['token']
        # get user with token
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(USERS_URL + TESTING_USERNAME)
        assert response.status_code == status.HTTP_200_OK
        
    def test_get_user_with_wrong_token(self):
        # incorrect user permission - token does not match the user being accessed
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user0_token.key)
        response = self.client.get(USERS_URL + TESTING_USERNAME)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_musicprofile_with_user_permission(self):
        response = self.client.post(LOGIN_URL, {'username': TESTING_USERNAME, 'refresh_token': TESTING_REFRESH_TOKEN})
        token = response.data['token']
        # get user with token
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(USERS_URL + "music_profile/" + TESTING_USERNAME)
        assert response.status_code == status.HTTP_200_OK
        assert 'music_profile_JSON' in response.data

    def test_get_musicprofile_with_wrong_token(self):
        # incorrect user permission - token does not match the user being accessed
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user0_token.key)
        response = self.client.get(USERS_URL + "music_profile/" + TESTING_USERNAME)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


##################
'''
    # needs a fresh access token
    def test_update_musicprofile(self):
        # one test to test our main backend functionality. This test takes a while...
        # using a user's own token, we fetch and upated the user's music profile (JSON)
        # this needs a valid access token and refresh token to work.
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        
        #access_token = get_access_token(spotify_app_credentials, MY_SPOTIFY_REFRESH_TOKEN)
        access_token = 'BQDHb5ebUR0gnxsXAa9BYh6RBXaKoVXumX4Wzgb4BVusRtQ1Het9UWgeS_lSC2bDezGAsMtfWFky7SPV8-nC0hBp3EbiSKvPBzK7uRM_1z6ESabyE7N4-GyYxtElRPcJisDLxPiruSs3Pqw9P0oETBKAV-oLj9NTFLK07lJJMbOQYIZ3c3VyA_S28VMNJpmNX9oIeWYvUaXYbUy4Jv-bLIKDKIsDBNmLmov1QumyYb8NV9K9rNrlyDfQVZzl'
        response = self.client.post(self.user0_musicprofile_url, {'access_token': access_token})
        assert response.status_code == status.HTTP_200_OK
        assert 'music_profile_JSON' in response.data
'''
##################

class TestSpotifyAppCredentials(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.spotify_app_credentials_url = API_URL + 'spotify-app-credentials/'
        

    def test_get_spotify_app_credentials_with_app_key(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + SECRET_APP_KEY)
        response = self.client.get(self.spotify_app_credentials_url)
        assert response.status_code == status.HTTP_200_OK
        assert 'clientId' in json.loads(response.content)


    def test_get_spotify_app_credentials_no_auth(self):
        self.client.credentials()
        response = self.client.get(self.spotify_app_credentials_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestConcertsAPICredentials(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.concerts_api_credentials_url = API_URL + 'concerts-APIs-credentials/'
        

    def test_get_concerts_api_credentials_url_with_app_key(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + SECRET_APP_KEY)
        response = self.client.get(self.concerts_api_credentials_url)
        assert response.status_code == status.HTTP_200_OK
        assert 'eventful' in json.loads(response.content)

    def test_get_concerts_api_credentials_url_no_auth(self):
        self.client.credentials()
        response = self.client.get(self.concerts_api_credentials_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN