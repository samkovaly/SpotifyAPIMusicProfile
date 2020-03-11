# Spotify API Music Profile Backend
Python version used: Python 3.7.6

check requirements.txt for requirements

STILL IN DEVELOPMENT | This is a backend API that connects to the Spotify API and generates a user 'music profile' consisting of their top artists and tracks
This data is returned to whoever requested it. It is meant for my front end app, which is here: github.com/samkovaly/My-Artists-App
Technologies include: Django & Django rest framework


1. pull .git
2. cd into folder
3. run python -m venv venv
4. run "venv/Scripts/activate"
5. run "pip install -r requirements.txt"
7. create local_secrets.py under spotifyAPIMusicProfile folder. It needs SECRET_KEY, DEBUG, ALLOWED_HOSTS, spotify_app_credentials_data and concert_events_API_keys defined
8. run "python manage.py migrate"
9. run "python manage.py createsuperuser"
10. run "python manage.py runserver"
11. test by going to .../admin and logging in