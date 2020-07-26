''''''

# Spotify Music Profile API
Open source back end code for my free app [My Artists](https://github.com/samkovaly/My-Artists-App). The app automatically analyzes user's Spotify accounts, finds their favorite artists, and shows concerts featuring these artists in a city near the user. This backend functions as the app's API. It holds user's accounts and their 'spotify music profile'. This profile is just a pandas data frame of all of the user's artists, with columns that pertain to info about the artist and also data on how this artist relates to this specific user (such as, 'top 100 all time favorite', or 'found in a playlist'). These dataframes are converted to JSON and returned to the front end app.


## Technologies
* Python
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
A POST request to api/users/music_profile/<str:username> will triger a spotify music profile rebuild. This does two things:
1. Scan the user's Spotify data via the Spotify API
2. Convert this to JSON and save it into the postgres database under the user.

A GET request to the same endpoint simply returns the music profile as it's saved in the database (JSON).



Python version used: Python 3.7.6

check requirements.txt for requirements

STILL IN DEVELOPMENT | This is a backend API that connects to the Spotify API and generates a user 'music profile' consisting of their top artists and tracks
This data is returned to whoever requested it. It is meant for my front end app, which is here: github.com/samkovaly/My-Artists-App
Technologies include: Django & Django rest framework


## License
[MIT License](/license)