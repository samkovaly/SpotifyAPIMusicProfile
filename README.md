# Spotify API Music Profile Backend
Python version used: Python 3.7.6

check requirements.txt for requirements

STILL IN DEVELOPMENT | This is a backend API that connects to the Spotify API and generates a user 'music profile' consisting of their top artists and tracks
This data is returned to whoever requested it. It is meant for my front end app, which is here: github.com/samkovaly/My-Artists-App
Technologies include: Django & Django rest framework


## INITIAL DEVELOPMENT SETUP
1. pull and cd into folder
3. run python -m venv venv
4. (windows) run venv/Scripts/activate
5. run pip install -r requirements.txt
6. install postgreSQL: https://www.postgresql.org/download/
7. create a database (via pgadmin or console)
8. add DATABASE_URL pointing to this postgres db to environmental variables
9. all the other environmental variables that settings.py needs.
10. ALLOWED_HOST should be your explicit local WiFi ip so expo (front end) can work can connect to it via LAN.
11. To get local IP:
    (Windows) run ipconfig on command prompt,
        under "wireless LAN adapter wifi", IPv4 Address.
12. run "python manage.py makemigrations musicProfile"
13. run "python manage.py migrate"
14. run "python manage.py createsuperuser"
15. run "python manage.py runserver {LOCAL_IP}:8000"
16. test by going to {LOCAL_IP}:8000/admin and logging in
17. in the  front-end code, add 'APIConfig.js' to the main directory and export API_IP='{LOCAL_IP}:8000' and API_MASTER_KEY=SECRET_APP_KEY that correlate to the backend. So that all front end requests look like: http://{LOCAL_IP}:8000/api/...