
import requests
import json


def fetch_user_id(access_token):
    print("fetching user id...")

    URL = "https://api.spotify.com/v1/me"
    header = {'Authorization' : "Bearer "+access_token}

    try:
        r = requests.get(URL, headers = header)
        r.raise_for_status()
        respDict = json.loads(r.text)
        user_id = respDict['id']
        return user_id

    except Exception as e:
        print("spotify_auth_functionality: error while fetchign user id: ", e)
        return None
    