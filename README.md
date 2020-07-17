# Spotify API Music Profile Backend
Python version used: Python 3.7.6

check requirements.txt for requirements

STILL IN DEVELOPMENT | This is a backend API that connects to the Spotify API and generates a user 'music profile' consisting of their top artists and tracks
This data is returned to whoever requested it. It is meant for my front end app, which is here: github.com/samkovaly/My-Artists-App
Technologies include: Django & Django rest framework


## DEVELOPMENT SETUP
1. pull and cd into folder
3. run python -m venv venv
4. (windows) run venv/Scripts/activate
5. run pip install -r requirements.txt
6. using local_secrets_template.py, create local_secrets.py under spotifyAPIMusicProfile folder. It needs SECRET_KEY, DEBUG, ALLOWED_HOSTS (using LOCAL_IP) and SECRET_APP_KEY (any uuid key) defined and both spotify_app_credentials and API_credentials to be filled in.
7. To get local IP:
    (Windows) run ipconfig on command prompt,
        under "wireless LAN adapter wifi", IPv4 Address.
8. add LOCAL_IP to 'ALLOWED HOSTS' in local_secrets.py
9. run "python manage.py makemigrations musicProfile"
10. run "python manage.py migrate"
11. run "python manage.py createsuperuser"
12. run "python manage.py runserver {LOCAL_IP}:8000"
13. test by going to {LOCAL_IP}:8000/admin and logging in
14. in the  front-end code, add 'APIConfig.js' to the main directory and export API_IP='{LOCAL_IP}:8000' and API_MASTER_KEY=SECRET_APP_KEY that correlate to the backend. So that all front end requests look like: http://{LOCAL_IP}:8000/api/...