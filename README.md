''''''

# Spotify Music Profile API
Open source back end code for my free app [My Artists](https://github.com/samkovaly/My-Artists-App). The app automatically analyzes user's Spotify accounts, finds their favorite artists, and shows concerts featuring these artists in a city near the user. This backend functions as the app's API. It holds user's accounts and their 'spotify music profile'. This profile is just a pandas data frame of all of the user's artists, with columns that pertain to info about the artist and also data on how this artist relates to this specific user (such as, 'top 100 all time favorite', or 'found in a playlist'). These dataframes are converted to JSON and returned to the front end app.


## Technologies
* Python (tested on 3.7.6)
* Django
* Django Rest Framework
* Pandas
* asyncio
* aiohttp
* Spotify API

The [front end React Native app of this project](https://github.com/samkovaly/My-Artists-App) uses:
* React Native
* Expo
* Redux
* Spotify API
* Seatgeek API
* Google Places Autocomplete

## How it works
* A POST request to api/users/music_profile/{str:username} will triger a spotify music profile rebuild. This does two things:
    1. Scan the user's Spotify data via the Spotify API. The user's top artists, their followed artists and artists found in their playlists are all collected and merged into one Pandas dataframe.
    2. This dataframe is then converted to JSON and save it into the postgres database under the user.
* A GET request to the same endpoint simply returns the music profile as it's saved in the database (JSON).

*This API is currently running on heroku to support the live app.* 

## Setup (tested only on windows)
1. Run `python -m venv venv`
1. Run `venv/Scripts/activate` (windows)
1. Run `pip install -r requirements.txt`
1. Make sure to have postgreSQL: https://www.postgresql.org/download/.
1. Create a postgres database (via pgadmin or console).
1. Get unique `DATABASE_URL` from this database and set it as an environmental variable.
1. Inside settings.py, there are many environmental variables needed. Set these all or hard code them in. If deploying to heroku, set heroku's config vars instead.
1. ALLOWED_HOST should be your explicit local IP so expo (front end) can connect to it via LAN..
1. To get local IP: (Windows) run ipconfig on command prompt, under "wireless LAN adapter wifi", IPv4 Address (for WiFi).
1. If deploying to heroku, must also run `heroku config:set DISABLE_COLLECTSTATIC=1`
1. Run `python manage.py makemigrations musicProfile`
1. Run `python manage.py migrate`
1. Run `python manage.py createsuperuser`
1. Run `python manage.py runserver {LOCAL_IP}:8000`
1. Test by going to `{LOCAL_IP}:8000/admin` (where `LOCAL_HOST` is the IP found above) and logging in with your superuser.
1. In the front-end code, add 'APIConfig.js' to the main directory and export `API_IP='{LOCAL_IP}:8000'` and `API_MASTER_KEY=SECRET_APP_KEY`. `SECRET_APP_KEY` must match this backend.


[MIT License](/license)