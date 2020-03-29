from django.http import JsonResponse

import requests
import asyncio
import aiohttp

import numpy as np
import pandas as pd
from pandas import json_normalize

import json
from functools import reduce



from random import randint
from time import sleep


def get_spotify_music_profile(request):
    

    spotifyAPI = SpotifyAPI(request)
    return spotifyAPI.get_music_profile()


class SpotifyAPI:
    REQUEST_EXCEPTION_MSG = "Spotify API Request Exception while fetching "

    REDUCE_PLAYLISTS = True
    MAX_PLAYLISTS = 5
    SAVE_DF_TO_FILE = True
    CACHING_MUSIC_PROFILE_FROM_CSV = True
    CACHED_ARTISTS_FILE = "cached_artists.csv"
    CACHED_TRACKS_FILE = "cached_tracks.csv"
    USER_PLAYLISTS_ONLY = True # don't change unless you want playlists I follow to also be included


    def __init__(self, request):
        access_token = request.headers['access-token']
        self.header = {'Authorization' : "Bearer "+access_token}
        #print('user access token:', access_token)
        self.user_id = self.fetch_user_id()

        self.artist_columns = []
        self.track_columns = []
        self.artists_dataframes = []
        self.tracks_dataframes = []

        self.artist_image_size_min = 100

        #self.test_increment = 0
        #self.caching_from_pre_agg = True



    def get_music_profile(self):

        if self.CACHING_MUSIC_PROFILE_FROM_CSV and self.get_cached_profile_csv():
            pass
        else:
            asyncio.run(self.collect_artists_and_tracks_dataframes())
            if self.SAVE_DF_TO_FILE:
                try:
                    self.artists_df.to_csv(self.CACHED_ARTISTS_FILE, index=False)
                    self.tracks_df.to_csv(self.CACHED_TRACKS_FILE, index=False)
                except:
                    print("can't save to new .csv, files are open")

        self.artists_df.drop(columns=['genres', 'tracks', 'image_size'], inplace=True)
        
        print("converting dataframes to JSON...")
        artists_json = self.get_artists_json(self.artists_df)
        tracks_json = self.get_tracks_json(self.tracks_df)

        with open("artists_json.json", 'w') as artists_json_file:
            artists_json_file.write(artists_json)
            
        
        with open("tracks_json.json", 'w') as tracks_json_file:
            tracks_json_file.write(tracks_json)
            


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


    def get_cached_profile_csv(self):
        try:
            self.artists_df = pd.read_csv(self.CACHED_ARTISTS_FILE)
            self.tracks_df = pd.read_csv(self.CACHED_TRACKS_FILE)
            return True
        
        except Exception as e:
            print('failed to find all cached files, must re-build:\n', e)
            return False


    def get_artists_json(self, artists_df):
        return artists_df.to_json(orient='records')

    def get_tracks_json(self, tracks_df):
        return tracks_df.to_json(orient='records')
        



    async def collect_artists_and_tracks_dataframes(self):

        # fetch artists and tracks together, due to how the Spotify API returns both
        print("collect_artists_and_tracks_dataframes()...")

        tasks = [self.fetch_top_artists("long_term"), self.fetch_top_artists("medium_term"), self.fetch_top_artists("short_term")
        , self.fetch_top_tracks("long_term"), self.fetch_top_tracks("medium_term"), self.fetch_top_tracks("short_term")
        , self.fetch_followed_artists(), self.fetch_saved_tracks(), self.get_all_playlists()]

        await asyncio.gather(*tasks)
        print("initial tasks (fetches) have finishing gathering..")
        print("initiating get_artists_master_df(), where full artist objects will be fetched..")
        self.artists_df = await self.get_artists_master_df()
        print("finished fetching full objects.")
        self.tracks_df = self.get_tracks_master_df()


    async def get_artists_master_df(self):

        artists_df = reduce(lambda left, right: pd.merge(left, right, how="outer"), self.artists_dataframes)
        artists_df = artists_df.drop_duplicates()

        # here, i fill in missing values
        # with a second gather operation
        artists_missing = artists_df[artists_df['image_size'].isnull()]
        artist_missing_list = artists_missing['id'].tolist()
        artists_full_df = await self.get_full_artist_dataframes(artist_missing_list)
        artists_df = pd.merge(artists_df, artists_full_df, how="outer")
        artists_df = artists_df.drop_duplicates()


        artists_df_transform = {}
        for column in self.artist_columns:
            artists_df_transform[column] = 'max'
        # takes 320 over 300 for example. some artists have 300 px images instead of 320 (don't know)
        artists_df_transform['image_size'] = 'min'
        artists_df_transform['image_url'] = 'first'
        def agg_track_list(tracks):         # set to remove duplicates
            track_list = [x for x in list(set(tracks)) if str(x) != 'nan']
            return track_list
        artists_df_transform['track.id'] = agg_track_list

        def agg_genres_list(genres):
            genre_list = [x for x in list(set(genres)) if str(x) != 'nan']
            return genre_list
        artists_df_transform['genres'] = agg_genres_list
        
        
        try:
            artists_df.to_csv("artists_df_before_final_agg.csv")
        except Exception as e:
            print(self.REQUEST_EXCEPTION_MSG + "art_final", e)


        artists_df = artists_df.groupby(['id', 'name']).agg(artists_df_transform)


        artists_df.rename(columns = {'track.id': 'tracks'}, inplace = True)
        artists_df[self.artist_columns] = artists_df[self.artist_columns].fillna(value=False)
        artists_df.reset_index(level=['id', 'name'], inplace = True)
        #artists_df = artists_df.reset_index()
        return artists_df


    def get_tracks_master_df(self):
        tracks_df = reduce(lambda left, right: pd.merge(left, right, how="outer"), self.tracks_dataframes)
        tracks_df = tracks_df.drop_duplicates()
        tracks_df[self.track_columns] = tracks_df[self.track_columns].fillna(value=False)
        #tracks_df = tracks_df.reset_index()
        return tracks_df





    async def fetch_top_artists(self, time_range):
        print('fetching top artists... ', time_range)
        self.artist_columns.append("top_artists_" + time_range)
        offsets = [0, 49]
        top_artists = []

        for offset in offsets:
            URL = "https://api.spotify.com/v1/me/top/artists?limit=50&offset="+str(offset)+"&time_range="+time_range
            resp_dict = await self.fetch_json_from_URL(URL = URL, name = "top artists({}):".format(time_range))
            # so if user's dont listen to enough artists in the short term,
            # then less than 100 short term artists are returned
            # in which case ['items'] equals [] and so we must check for this
            # and just simply do nothing when it happens
            if resp_dict['items']:
                artists_df = self.extract_full_artist_from_json(resp_dict['items'])
                artists_df["top_artists_"+time_range] = True

                top_artists.append(artists_df)

        self.artists_dataframes.append(pd.concat(top_artists))
        


    async def fetch_top_tracks(self, time_range):
        print('fetching top tracks... ', time_range)
        self.track_columns.append("top_tracks_" + time_range)

        offsets = [0, 49]
        all_artists = []
        all_tracks = []
        
        for offset in offsets:
            URL = "https://api.spotify.com/v1/me/top/tracks?limit=50&offset="+str(offset)+"&time_range="+time_range
            resp_dict = await self.fetch_json_from_URL(URL = URL, name = "artists from top tracks({})".format(time_range))
            if resp_dict['items']:
                data = json_normalize(data = resp_dict['items'], record_path=['artists'], meta=['id', 'name'], meta_prefix='track.')


                # take care of tracks first, much simpler
                tracks_df = self.reduce_tracks_df(data)
                tracks_df["top_tracks_"+time_range] = True

                artists_df = data[['id', 'name', 'track.id']]

                all_artists.append(artists_df)
                all_tracks.append(tracks_df)

        self.artists_dataframes.append(pd.concat(all_artists))
        self.tracks_dataframes.append(pd.concat(all_tracks).drop_duplicates(subset = 'id'))
    

    async def fetch_followed_artists(self):
        print('fetching followed artists... ')
        self.artist_columns.append("followed_artist")

        next = "https://api.spotify.com/v1/me/following?type=artist&limit=50&offset=0"
        followed_artists = []

        while next:
            resp_dict = await self.fetch_json_from_URL(URL = next, name = "followed artists")
            artists_df = self.extract_full_artist_from_json(resp_dict['artists']['items'])
            artists_df['followed_artist'] = True
            followed_artists.append(artists_df)

            next = resp_dict['artists']['next']

        self.artists_dataframes.append(pd.concat(followed_artists))

    async def fetch_saved_tracks(self):
        print('fetching saved tracks... ')
        self.track_columns.append("saved_tracks")

        next = "https://api.spotify.com/v1/me/tracks?limit=50&offset=0"
        all_artists = []
        all_tracks = []
        
        while next:
            resp_dict = await self.fetch_json_from_URL(URL = next, name = "saved tracks")
            data = json_normalize(data = resp_dict['items'], record_path=['track', 'artists'], meta=[['track', 'name'], ['track', 'id']])

            tracks_df = self.reduce_tracks_df(data)
            tracks_df["saved_tracks"] = True
            artists_df = data[['id', 'name', 'track.id']]

            all_artists.append(artists_df)
            all_tracks.append(tracks_df)
            next = resp_dict['next']

        self.artists_dataframes.append(pd.concat(all_artists))
        self.tracks_dataframes.append(pd.concat(all_tracks).drop_duplicates(subset = 'id'))


    async def fetch_playlists(self):
        print('fetch_playlists...')
        playlists_all = []
        next = "https://api.spotify.com/v1/me/playlists?limit=50&offset=0"

        while next:
            resp_dict = await self.fetch_json_from_URL(URL = next, name = "playlists")
            playlists_full = json_normalize(resp_dict['items'])
            playlists = playlists_full[['id', 'owner.id']]

            if self.USER_PLAYLISTS_ONLY:
                playlists = playlists[playlists['owner.id'] == self.user_id]

            playlists.drop('owner.id', axis=1, inplace=True)
            playlists_all.append(playlists)
            next = resp_dict['next']

        return pd.concat(playlists_all)

    async def get_all_playlists(self):
        playlists = await self.fetch_playlists()
        self.track_columns.append("playlist")

        tracks = []
        artists = []

        # for easier debugging
        if self.REDUCE_PLAYLISTS:
            print("REDUCE_PLAYLISTS enabled")
            playlists = playlists[0:self.MAX_PLAYLISTS]


        print('fetching', len(playlists), 'playlists...')

        tasks = [self.fetch_playlist(playlistID) for playlistID in playlists['id']]
        playlistDatas = await asyncio.gather(*tasks)

        for playlistData in playlistDatas:
            artists.append(playlistData[0])
            tracks.append(playlistData[1])

        self.artists_dataframes.append(pd.concat(artists))
        self.tracks_dataframes.append(pd.concat(tracks))


    async def fetch_playlist(self, ID):
        #print('fetchin_playlist({})'.format(ID))

        next = "https://api.spotify.com/v1/playlists/"+ID+"/tracks?limit=100&offset=0"
        all_artists = []
        all_tracks = []
        while next:
            resp_dict = await self.fetch_json_from_URL(URL = next, name = "tracks from playlist")
            data = json_normalize(data = resp_dict['items'], record_path=['track', 'artists'], meta=[['track', 'name'], ['track', 'id']])
            artists_df = data[['id', 'name', 'track.id']]

            tracks_df = self.reduce_tracks_df(data)
            tracks_df["playlist"] = True

            all_artists.append(artists_df)
            all_tracks.append(tracks_df)
            next = resp_dict['next']

        all_artists = pd.concat(all_artists)
        all_tracks = pd.concat(all_tracks).drop_duplicates(subset = 'id')
        return all_artists, all_tracks




    ''' takes a list of artist IDs, fetches the full artist objects from spotify using these IDs (50 at a time max),
        calls extract_full_artist_from_json on the returns and returns a dataframe with all the columns needed
        for the mobile app '''
    async def get_full_artist_dataframes(self, all_IDs):
        print(f"get_all_details_on({len(all_IDs)})_artists...")

        ID_segments = self.split_into_N(all_IDs, 50)
        tasks = [self.fetch_full_artists(IDs) for IDs in ID_segments]
        artist_dataframes = await asyncio.gather(*tasks)
        return pd.concat(artist_dataframes)


    ''' IDs should be of length 50 or less '''
    async def fetch_full_artists(self, IDs):
        print(f'fetching full artist details for {len(IDs)} artists')
        print(f"  first aritst ID is {IDs[0]}")
        URL = "https://api.spotify.com/v1/artists"

        resp_dict = await self.fetch_json_from_URL(
            URL = URL, 
            params = [('ids', ",".join(IDs))],
            name = "full artist objects")
        try:
            artist_df = self.extract_full_artist_from_json(resp_dict['artists'])
        except Exception as e:
            print(f"artist IDs starting with {IDs[0]} has returned with resp_dict of:{resp_dict}")
            print('exception in fetch_full_artists, resp_dict is messed up:', e)


        return artist_df


    def split_into_N(self, _list, N):
        return [_list[i * N:(i + 1) * N] for i in range((len(_list) + N - 1) // N )]


    ''' json_data must be a JSON array of full artist objects. Returns a dataframe of all the objects with
        columns: id, name, genres, image_url, image_size'''
    def extract_full_artist_from_json(self, json_data):

        artists_genres = json_normalize(data = json_data, record_path='genres', meta=['id', 'name'])
        artists_images = json_normalize(data = json_data, record_path='images', meta=['id', 'name'])

        artists_df = pd.merge(artists_genres, artists_images, how="outer")

        # filter out other sizes that we don't want
        artists_df = artists_df[artists_df.height >= self.artist_image_size_min]

        # don't need height and width, only size since they are the same
        artists_df = artists_df.drop(['height'], axis=1)

        # genres columns defaults to '0' since we are extracting an array in the record_path ('genres'),
        # an array of strigs, not objects
        artists_df = artists_df.rename(columns={0: 'genres', 'url': 'image_url', 'width': 'image_size'})
        return artists_df



    ''' takes full tracks dataframe and takes only the track's id and name columns '''
    def reduce_tracks_df(self, full_tracks_df):
        tracks_df = full_tracks_df[['track.id', 'track.name']]
        tracks_df = tracks_df.rename(columns={'track.id': 'id', 'track.name': 'name'})
        return tracks_df


    ''' fetch user id is implemented with requests library instead of asyncio '''
    def fetch_user_id(self):
        print("fetching user id...")
        #resp_dict = await self.fetch_json_from_URL(URL = "https://api.spotify.com/v1/me", name = "user id")
        #return resp_dict['id']

        URL = "https://api.spotify.com/v1/me"
        try:
            r = requests.get(URL, headers = self.header)
            r.raise_for_status()
            respDict = json.loads(r.text)

            user_id = respDict['id']
            return user_id
        except Exception as e:
            print(self.REQUEST_EXCEPTION_MSG + "user id:", e)
        


    ''' basic fetch json from URL function implemented with aiohttp async. (need asyncio gath to call). '''
    async def fetch_json_from_URL(self, URL, params = None, name = ""):
        r = None
        try:
            async with aiohttp.ClientSession(raise_for_status=True) as session:
                r = await session.get(URL, params = params, headers = self.header)
                #print(URL)
                resp_dict = json.loads(await r.text())
                return resp_dict

        except Exception as e:
            print(self.REQUEST_EXCEPTION_MSG + name, URL, ":", e)
            print("\nrequest status: ", r.status, "\n")
            print("\nrequest reason: ", r.reason, "\n")
