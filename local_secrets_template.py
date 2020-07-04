
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


# LOCAL_IP is my ip address, directly accessable by the PC and phone testing via the wifi

# MUST START DEV SERVER WTIH 'python manage.py runserver {LOCAL_IP}:8000'
LOCAL_IP = ''
# MUST FETCH THIS API with fetch('http://{LOCAL_IP}:8000/api/...'
ALLOWED_HOSTS = [LOCAL_IP]

# so the app can fetch app credentials and 3rd party concert API keys from this backend.
SECRET_APP_KEY = ""

# client app credentials
spotify_app_credentials = {
    'clientId': '',
    'clientSecret': '',
    'redirectUri': ''
}

# third party API keys for the client app to use
API_credentials = {
    "seatgeek": {
        "client_id": "",
    },
    "googlePlacesAPI": {
        "key": '',
    },
}