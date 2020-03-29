from rest_framework.test import APITestCase

# Create your tests here.



from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory




API_URL = '/api/'
AUTH_URL = '/auth/'
USERS_URL = API_URL+'users/'

APP_KEY = 'LOOL'

class TestUsers(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_superuser('admin', 'myemail@test.com', 'adminboy')
        self.admin_token = Token.objects.create(user=self.admin_user)

        self.user0_username = 'mike'
        self.user0_password = 'pass'
        self.user0 = User.objects.create_user(username=self.user0_username, password=self.user0_password)
        self.user0_token = Token.objects.create(user=self.user0)

        self.username1 = 'username1'
        self.password1 = 'password1'
        self.username2 = 'username2'
        self.password2 = 'password2'


        
    # 401 when HasKeyOrIsAdmin fails, 400 when serializer.is_valid() fails
    def test_register_without_credentials(self):
        response = self.client.post(USERS_URL, {'username': self.username1, 'password': self.password1})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        

    def test_register_with_app_key(self):
        # user register with secret key from app
        response = self.client.post(USERS_URL, {'username': self.username1, 'password': self.password1, 'app_key': APP_KEY})
        assert response.status_code == status.HTTP_201_CREATED

    def test_register_with_bad_app_key(self):
        response = self.client.post(USERS_URL, {'username': self.username1, 'password': self.password1, 'app_key': 'random lol'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


    def test_get_all_users_with_admin_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.get(USERS_URL)
        num_users = len(response.data)
        assert num_users > 0


    # get user auth token for user0 and make sure it works
    # aka: user login
    def test_user_auth_token(self):
        response = self.client.post(AUTH_URL, {'username': self.user0_username, 'password': self.user0_password})
        assert response.status_code == status.HTTP_200_OK

        token = response.data['token']
        assert token is not None
        
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.get(USERS_URL + self.user0_username)
        assert response.status_code == status.HTTP_200_OK


class TestUserMusicProfiles(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin_user = User.objects.create_superuser('admin', 'myemail@test.com', 'adminboy')
        self.admin_token = Token.objects.create(user=self.admin_user)

        self.user0_username = 'mike'
        self.user0_password = 'pass'
        self.user0 = User.objects.create_user(username=self.user0_username, password=self.user0_password)
        self.user0_token = Token.objects.create(user=self.user0)
        self.user0_url = USERS_URL + self.user0_username
        self.user0_musicprofile_url = self.user0_url + '/music_profile'

        self.user1_username = 'miguel'
        self.user1_password = 'pass'
        self.user1 = User.objects.create_user(username=self.user1_username, password=self.user1_password)
        self.user1_token = Token.objects.create(user=self.user1)
        self.user1_url = USERS_URL + self.user1_username
        self.user1_musicprofile_url = self.user1_url + '/music_profile'

    
    def test_get_user_with_user_permission(self):
        # correct user permission
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user0_token.key)
        response = self.client.get(self.user0_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == self.user0_username
        assert 'userprofile' in response.data
        
        
    def test_get_user_with_admin_permission(self):
        # correct user permission because using admin token
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.get(self.user0_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == self.user0_username
        assert 'userprofile' in response.data
        
    def test_get_user_with_wrong_token(self):
        # incorrect user permission - token does not match the user being accessed
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user1_token.key)
        response = self.client.get(self.user0_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED




    def test_get_musicprofile_with_user_permission(self):
        # correct user permission
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user0_token.key)
        response = self.client.get(self.user0_musicprofile_url)
        assert response.status_code == status.HTTP_200_OK
        assert 'music_profile_JSON' in response.data
        
        
    def test_get_musicprofile_with_admin_permission(self):
        # correct user permission because using admin token
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.get(self.user0_musicprofile_url)
        assert response.status_code == status.HTTP_200_OK
        assert 'music_profile_JSON' in response.data
        
    def test_get_musicprofile_with_wrong_token(self):
        # incorrect user permission - token does not match the user being accessed
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user1_token.key)
        response = self.client.get(self.user0_musicprofile_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED



class TestStaticJSONRetrievals(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_spotify_app_credentials(self):
        url = '/concert-APIs-credentials/'
        #self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user1_token.key)
        response = self.client.get(url)
        print(response.content)
        #'clientId': '6950e58caba04226b62bcb68ab165d97',


    def test_get_concert_API_keys(self):
        pass