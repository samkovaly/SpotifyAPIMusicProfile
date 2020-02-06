from django.http import JsonResponse

import requests
import asyncio
import aiohttp

import numpy as np
import pandas as pd
from pandas.io.json import json_normalize

import json
from functools import reduce

def get_spotify_music_profile(request):

    spotifyAPI = SpotifyAPI(request)
    return spotifyAPI.get_music_profile()


class SpotifyAPI:
    REQUEST_EXCEPTION_MSG = "Spotify API Request Exception while fetching "

    REDUCE_TIME_DEBUG = False
    SAVE_DF_TO_FILE = False
    USER_PLAYLISTS_ONLY = True # don't change unless you want playlists I follow to also be included


    def __init__(self, request):
        access_token = request.headers['access-token']
        self.header = {'Authorization' : "Bearer "+access_token}
        self.user_id = self.fetch_user_id()

        self.artist_columns = []
        self.track_columns = []
        self.artists_dataframes = []
        self.tracks_dataframes = []

    def get_music_profile(self):

        try:
            asyncio.run(self.collect_artists_and_tracks_dataframes())
        except Exception as e:
            print("excetion while running asyncio.run(self.collect_artists_and_tracks_dataframes())...", e)


        artists_df = self.get_artists_master_df()
        tracks_df = self.get_tracks_master_df()

        if self.SAVE_DF_TO_FILE:
            artists_df.to_csv('head_artists_df.csv', index=False)
            tracks_df.to_csv('head_tracks_df.csv', index=False)

        artists_json = self.get_artists_json(artists_df)
        tracks_json = self.get_tracks_json(tracks_df)

        ''' artists_json: dataframe of:
        { 
            name: ""
            id: ""
            top_artists_long_term: T/F
            top_artists_medium_term: T/F
            top_artists_short_term: T/F
            followed_artist: T/F
            tracks: [ "...", "...", ...]
        }
        '''
        music_profile = {
            "artists" : artists_json,
            "tracks" : tracks_json,
        }
        print("returning JSON response")
        return JsonResponse(music_profile)



    def get_artists_json(self, artists_df):
        return artists_df.to_json(orient='records')

    def get_tracks_json(self, tracks_df):
        return tracks_df.to_json(orient='records')
        



    async def collect_artists_and_tracks_dataframes(self):

        # fetch artists and tracks together, due to how the Spotify API returns both
        tasks = [self.fetch_top_artists("long_term"), self.fetch_top_artists("medium_term"), self.fetch_top_artists("short_term")
        , self.fetch_top_tracks("long_term"), self.fetch_top_tracks("medium_term"), self.fetch_top_tracks("short_term")
        , self.fetch_followed_artists(), self.fetch_saved_tracks(), self.get_all_playlists()]

        await asyncio.gather(*tasks)
    

    def get_artists_master_df(self):
        artists_df = reduce(lambda left, right: pd.merge(left, right, how="outer"), self.artists_dataframes)
        artists_df = artists_df.drop_duplicates()

        artists_df_transform = {}
        for column in self.artist_columns:
            artists_df_transform[column] = 'max'
        
        def agg_track_list(tracks):
            track_list = [x for x in list(tracks) if str(x) != 'nan']
            return track_list

        artists_df_transform['track.id'] = agg_track_list
        
        artists_df = artists_df.groupby(['id', 'name']).agg(artists_df_transform)
        artists_df.rename(columns = {'track.id': 'tracks'}, inplace = True)
        artists_df[self.artist_columns] = artists_df[self.artist_columns].fillna(value=False)
        artists_df.reset_index(level=['id', 'name'], inplace = True)
        return artists_df


    def get_tracks_master_df(self):
        tracks_df = reduce(lambda left, right: pd.merge(left, right, how="outer"), self.tracks_dataframes)
        tracks_df = tracks_df.drop_duplicates()
        tracks_df[self.track_columns] = tracks_df[self.track_columns].fillna(value=False)
        return tracks_df



    async def fetch_top_artists(self, time_range):
        print('fetching top artists... ', time_range)
        self.artist_columns.append("top_artists_" + time_range)
        try:
            offsets = [0, 49]
            top_artists = []
            async with aiohttp.ClientSession(raise_for_status=True) as session:
                for offset in offsets:
                    URL = "https://api.spotify.com/v1/me/top/artists?limit=50&offset="+str(offset)+"&time_range="+time_range
                    r = await session.get(URL, headers = self.header)
                    respDict = json.loads(await r.text())

                    artists_full = json_normalize(respDict['items'])
                    artists = artists_full[['id', 'name']]
                    artists["top_artists_"+time_range] = True


                    top_artists.append(artists)
            
            self.artists_dataframes.append(pd.concat(top_artists))
        
        except Exception as e:
            print(self.REQUEST_EXCEPTION_MSG + "top artists", e)




    async def fetch_top_tracks(self, time_range):
        print('fetching top tracks... ', time_range)
        self.track_columns.append("top_tracks_" + time_range)


        try:
            offsets = [0, 49]
            all_artists = []
            all_tracks = []
            async with aiohttp.ClientSession(raise_for_status=True) as session:
                for offset in offsets:
                    URL = "https://api.spotify.com/v1/me/top/tracks?limit=50&offset="+str(offset)+"&time_range="+time_range
                    r = await session.get(URL, headers = self.header)
                    respDict = json.loads(await r.text())
                    
                    data = json_normalize(data = respDict['items'], record_path=['artists'], meta=['id', 'name'], meta_prefix='track.')
                    artists = data[['id', 'name', 'track.id']]

                    tracks = data[['track.id', 'track.name']]
                    tracks = tracks.rename(columns={'track.id': 'id', 'track.name': 'name'})
                    tracks["top_tracks_"+time_range] = True

                    all_artists.append(artists)
                    all_tracks.append(tracks)

            self.artists_dataframes.append(pd.concat(all_artists))
            self.tracks_dataframes.append(pd.concat(all_tracks).drop_duplicates(subset = 'id'))
        
        except Exception as e:
            print(self.REQUEST_EXCEPTION_MSG + "artists from top tracks", e)


    async def fetch_followed_artists(self):
        print('fetching followed artists... ')
        self.artist_columns.append("followed_artist")

        try:
            async with aiohttp.ClientSession(raise_for_status=True) as session:
                next = "https://api.spotify.com/v1/me/following?type=artist&limit=50&offset=0"
                followed_artists = []
                while next:
                    r = await session.get(next, headers = self.header)
                    respDict = json.loads(await r.text())

                    artists_full = json_normalize(respDict['artists']['items'])
                    artists = artists_full[['id', 'name']]
                    artists['followed_artist'] = True
                    followed_artists.append(artists)

                    next = respDict['artists']['next']

            self.artists_dataframes.append(pd.concat(followed_artists))

        except Exception as e:
            print(self.REQUEST_EXCEPTION_MSG + "followed artists", e)


    async def fetch_saved_tracks(self):
        print('fetching saved tracks... ')
        self.track_columns.append("saved_tracks")


        try:
            next = "https://api.spotify.com/v1/me/tracks?limit=50&offset=0"
            all_artists = []
            all_tracks = []
            async with aiohttp.ClientSession(raise_for_status=True) as session:
                while next:
                    r = await session.get(next, headers = self.header)
                    respDict = json.loads(await r.text())

                    data = json_normalize(data = respDict['items'], record_path=['track', 'artists'], meta=[['track', 'name'], ['track', 'id']])

                    artists = data[['id', 'name', 'track.id']]

                    tracks = data[['track.id', 'track.name']]
                    tracks = tracks.rename(columns={'track.id': 'id', 'track.name': 'name'})
                    tracks["saved_tracks"] = True


                    all_artists.append(artists)
                    all_tracks.append(tracks)
                    next = respDict['next']


            self.artists_dataframes.append(pd.concat(all_artists))
            self.tracks_dataframes.append(pd.concat(all_tracks).drop_duplicates(subset = 'id'))

        except Exception as e:
            print(self.REQUEST_EXCEPTION_MSG + "saved tracks", e)


    async def get_all_playlists(self):
        playlists = await self.fetch_playlists()
        self.track_columns.append("playlist")

        tracks = []
        artists = []

        print('fetching', len(playlists), 'playlists...')

        tasks = [self.fetch_playlist(playlistID) for playlistID in playlists['id']]
        playlistDatas = await asyncio.gather(*tasks)

        for playlistData in playlistDatas:
            artists.append(playlistData[0])
            tracks.append(playlistData[1])
        
        '''
        for playlistID in playlists['id']:
            playlistData = await self.fetch_playlist(playlistID)
            artists.append(playlistData[0])
            tracks.append(playlistData[1])
        '''

        self.artists_dataframes.append(pd.concat(artists))
        self.tracks_dataframes.append(pd.concat(tracks))


    async def fetch_playlists(self):
        print('fetch_playlists...')

        try:
            async with aiohttp.ClientSession(raise_for_status=True) as session:
                next = "https://api.spotify.com/v1/me/playlists?limit=50&offset=0"
                playlists_all = []
                while next:
                    r = await session.get(next, headers = self.header)
                    respDict = json.loads(await r.text())
                    
                    playlists_full = json_normalize(respDict['items'])
                    playlists = playlists_full[['id', 'owner.id']]
                    if self.USER_PLAYLISTS_ONLY:
                        playlists = playlists[playlists['owner.id'] == self.user_id]

                    playlists.drop('owner.id', axis=1, inplace=True)
                    playlists_all.append(playlists)


                    next = respDict['next']

            return pd.concat(playlists_all)

        except Exception as e:
            print(self.REQUEST_EXCEPTION_MSG + "playlists", e)


    async def fetch_playlist(self, ID):
        print('fetchin_playlist({})'.format(ID))
        
        try:
            async with aiohttp.ClientSession(raise_for_status=True) as session:
                next = "https://api.spotify.com/v1/playlists/"+ID+"/tracks?limit=100&offset=0"
                all_artists = []
                all_tracks = []
                while next:
                    r = await session.get(next, headers = self.header)
                    respDict = json.loads(await r.text())

                    data = json_normalize(data = respDict['items'], record_path=['track', 'artists'], meta=[['track', 'name'], ['track', 'id']])

                    artists = data[['id', 'name', 'track.id']]

                    tracks = data[['track.id', 'track.name']]
                    tracks = tracks.rename(columns={'track.id': 'id', 'track.name': 'name'})
                    tracks["playlist"] = True

                    all_artists.append(artists)
                    all_tracks.append(tracks)
                    next = respDict['next']

                all_artists = pd.concat(all_artists)
                all_tracks = pd.concat(all_tracks).drop_duplicates(subset = 'id')
            
            return all_artists, all_tracks

        except Exception as e:
            print(self.REQUEST_EXCEPTION_MSG + "tracks from playlist", e)


    def fetch_user_id(self):
        print("fetching user id...")
        try:
            URL = "https://api.spotify.com/v1/me"
            r = requests.get(URL, headers = self.header)
            r.raise_for_status()
            respDict = json.loads(r.text)

            user_id = respDict['id']
            return user_id
        except Exception as e:
            print(self.REQUEST_EXCEPTION_MSG + "saved tracks", e)


