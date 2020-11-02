''''''

# Spotify Music Profile API
Open source back end code for the react native mobile app My Artists. The app automatically analyzes user's Spotify accounts, finds their favorite artists, and shows concerts featuring these artists in a city near the user. This code functions as the app's backend API. It holds user's accounts and their *Spotify music profile*. This profile is just a Python Pandas dataframe of all the user's artists. The columns are a mix of information about the artist and data on how the artist relates to this specific user. For example: ```id```, ```name```, ```top_artists_long_term```, ```top_artists_short_term``` and ```playlist```). This dataframe is converted to JSON and returned to the front end app. The API also lets users save retrieve and delete their favorite concerts that they have found.
<br/>
[Apple App Store](https://apps.apple.com/us/app/my-artists-only/id1525832462)
<br/>
[Google Play Store](https://play.google.com/store/apps/details?id=xilernet.myartists)
<br/>
[Frontend React Native](https://github.com/samkovaly/My-Artists-App)


## Technologies
* Python (tested on 3.7.6)
* Django 3
* Django Rest Framework
* Pandas
* asyncio
* aiohttp
* Spotify API

The [front end React Native app of this project](https://github.com/samkovaly/My-Artists-App) uses:
* Expo
* React Native with React Hooks
* Redux & Thunk middleware
* React Navigation 5
* Spotify API
* Seatgeek API
* Google Places Autocomplete API

## How it works
**Register**: A POST request to ```/api/register``` requires the users Spotify username, working access token and refresh token. The refresh token acts as the user's password. If the the user already exists, it verifies the data against itself (access token must match username) and updates the refresh token / password.

**Login**: A POST request to ```/api/login``` returns a user's auth token.

**Analyzing Spotify**: A POST request to ```/api/users/music_profile/<str:username>``` will trigger a *spotify music profile* rebuild. This does two things:
1. Scan the user's Spotify data via the Spotify API. The user's top artists, their followed artists and artists found in their playlists are all collected and merged into one Pandas dataframe.
1. This dataframe is then converted to JSON and save it into the postgres database under the user.

**Fetching the music profile**: A GET request to the same ```/api/users/music_profile/<str:username>``` endpoint returns the user's JSON music profile that is saved in the database.

**Interested Concerts**: <br>
A POST to ```users/interested_concerts/<str:username>``` adds an ```InterestedConcert``` to the database that simply holds the Seatgeek concet ID.<br>
A GET to ```users/interested_concerts/<str:username>``` returns all the concerts for ```username```.<br>
A DELETE to ```users/interested_concerts/<str:username>/<str:concert_id>``` will delete it from the database.

*This API is currently running on Heroku to support the live app.* 

## Setup (tested only on windows)
1. Run `python -m venv venv`
1. Run `venv/Scripts/activate` (windows)
1. Run `pip install -r requirements.txt`
1. Make sure to have postgreSQL: https://www.postgresql.org/download/.
1. Create a postgres database (via pgadmin or console).
1. Get unique `DATABASE_URL` from this database and set it as an environmental variable.
1. Inside settings.py, there are many environmental variables needed. Set these all or hard code them in. If deploying to heroku, set heroku's config vars instead.
1. ALLOWED_HOST should be your explicit local IP so expo (front end) can connect to it via LAN..
1. To get local IP: (Windows) run ipconfig on command prompt, under "wireless LAN adapter WiFi", "IPv4 Address".
1. If deploying to heroku, must also run `heroku config:set DISABLE_COLLECTSTATIC=1`
1. Run `python manage.py makemigrations musicProfile`
1. Run `python manage.py migrate`
1. Run `python manage.py createsuperuser`
1. Run `python manage.py runserver {LOCAL_IP}:8000`
1. Test by going to `{LOCAL_IP}:8000/admin` (where `LOCAL_HOST` is the IP found above) and logging in with your superuser.
1. In the front-end code, add 'APIConfig.js' to the main directory and export `API_IP='{LOCAL_IP}:8000'` and `API_MASTER_KEY=SECRET_APP_KEY`. `SECRET_APP_KEY` must match this backend.


[MIT License](/license)
