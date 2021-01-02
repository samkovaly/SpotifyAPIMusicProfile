from django.http import JsonResponse

import requests
import asyncio
import aiohttp

import numpy as np
import pandas as pd
from pandas import json_normalize

import json
from functools import reduce

import unidecode

from random import randint
from time import sleep

import traceback
import sys

import random

import logging

def get_spotify_music_profile(request):
    spotifyAPI = SpotifyAPI(request)
    try:
        music_profile = spotifyAPI.get_music_profile()
        return music_profile
    except Exception as e:
        # traceback.format_exc()
        print('GLOBAL EXCEPTION - BAD. RETURNING ERROR TO FRONT END')
        logging.exception("music profile refresh exception")
        error_report = {
            'error': {
                'message': str(e),
                'status': 500,
            }
        }
        return error_report


class SpotifyAPI:
    REQUEST_EXCEPTION_MSG = "Spotify API Request Exception while fetching "
    SAVE_PROFILE_AS_CSV = False


    USER_PLAYLISTS_ONLY = True # don't change unless you want playlists a user follows to also be included


    def __init__(self, access_token):
        self.header = {'Authorization' : "Bearer "+access_token}
        self.user_id = self.fetch_user_id()


        self.artist_columns = []
        self.track_columns = []
        self.artists_dataframes = []
        self.tracks_dataframes = []


    def get_music_profile(self):
        asyncio.run(self.collect_artists_and_tracks_dataframes())
        
        print("converting dataframes to JSON...")

        print(f'returning { self.artists_df.shape[0] } artists and { self.tracks_df.shape[0] } tracks')


        if self.SAVE_PROFILE_AS_CSV:
            self.artists_df.to_csv('artists_df.csv')
            self.tracks_df.to_csv('tracks_df.csv')

        artists_json = self.get_artists_json(self.artists_df)
        tracks_json = self.get_tracks_json(self.tracks_df)


        music_profile = {
            "artists" : artists_json,
            "tracks" : tracks_json,
        }

        return music_profile



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

        if self.artists_dataframes == []:
            return pd.DataFrame()

        artists_df = None
        if len(self.artists_dataframes) > 1:
            artists_df = reduce(lambda left, right: pd.merge(left, right, how="outer"), self.artists_dataframes)
        else:
            artists_df = self.artists_dataframes[0]

        artists_df = artists_df.drop_duplicates()

        if 'id' not in artists_df:
            return pd.DataFrame()

        # add all columns needed if we don't have them yet
        for col in self.artist_columns:
            if col not in artists_df:
                artists_df[col] = np.NaN

        if 'track.id' not in artists_df:
            artists_df['track.id'] = np.NaN

        # here, i fill in missing values
        # with a second gather operation
        if 'image' in artists_df:
            artists_missing = artists_df[artists_df['image'].isnull()]
        else:
            artists_missing = artists_df

        missing_ids = artists_missing['id'].tolist()
        missing_ids = list(set(missing_ids))

        if len(missing_ids) > 0:
            artists_full_df = await self.get_full_artist_dataframes(missing_ids)
            artists_df = pd.merge(artists_df, artists_full_df, how="outer")
        
        artists_df = artists_df.drop_duplicates()

        artists_df['smallImage'] = artists_df['image']
        artists_df['bigImage'] = artists_df['image']
        artists_df.drop('image', axis = 1)

        artists_df_transform = {}
        for column in self.artist_columns:
            artists_df_transform[column] = 'max'


        artists_df_transform['bigImage'] = 'first'
        artists_df_transform['smallImage'] = 'last'
        artists_df_transform['uri'] = 'first'

        def agg_track_list(tracks):         # set to remove duplicates
            track_list = [x for x in list(set(tracks)) if str(x) != 'nan']
            return track_list
        artists_df_transform['track.id'] = agg_track_list

        def agg_genres_list(genres):
            genre_list = [x for x in list(set(genres)) if str(x) != 'nan']
            return genre_list
        artists_df_transform['genres'] = agg_genres_list

        artists_df = artists_df.groupby(['id', 'name']).agg(artists_df_transform)


        artists_df.rename(columns = {'track.id': 'tracks'}, inplace = True)
        artists_df[self.artist_columns] = artists_df[self.artist_columns].fillna(value=False)
        artists_df.reset_index(level=['id', 'name'], inplace = True)

        # add artist's tracks_length
        def get_tracks_len(row):
            return len(list(row['tracks']))
        artists_df['tracks_length'] = artists_df.apply(get_tracks_len, axis=1)

        # add artist's genres_length
        def get_genres_len(row):
            return len(list(row['genres']))
        artists_df['genres_length'] = artists_df.apply(get_genres_len, axis=1)

        def get_ascii_artist_name(row):
            return unidecode.unidecode(row['name'])
        artists_df['name_ascii'] = artists_df.apply(get_ascii_artist_name, axis=1)

        return artists_df


    def get_tracks_master_df(self):
        
        if self.tracks_dataframes == []:
            return pd.DataFrame()
        
        tracks_df = reduce(lambda left, right: pd.merge(left, right, how="outer"), self.tracks_dataframes)
        tracks_df = tracks_df.drop_duplicates()

        
        if 'id' not in tracks_df:
            return pd.DataFrame()

        tracks_df[self.track_columns] = tracks_df[self.track_columns].fillna(value=False)

        tracks_df_transform = {}
        tracks_df_transform['image_size'] = 'min'
        tracks_df_transform['image_url'] = 'first'

        #tracks_df_transform['top_tracks_short_term'] = 'first'
        #tracks_df_transform['saved_tracks'] = 'first'
        #tracks_df_transform['top_tracks_medium_term'] = 'first'
        #tracks_df_transform['top_tracks_long_term'] = 'first'
        #tracks_df_transform['playlist'] = 'first'


        tracks_df = tracks_df.groupby(['id', 'name', 'uri']).agg(tracks_df_transform)
        tracks_df.reset_index(level=['id', 'name', 'uri'], inplace = True)

        return tracks_df


    async def fetch_top_artists(self, time_range):
        print('fetching top artists... ', time_range)
        self.artist_columns.append("top_artists_" + time_range)
        self.artist_columns.append("top_artists_" + time_range + "_ranking")
        offsets = [0, 49]
        top_artists = []

        for offset in offsets:
            URL = "https://api.spotify.com/v1/me/top/artists?limit=50&offset="+str(offset)+"&time_range="+time_range
            resp_dict = await self.fetch_json_from_URL(URL = URL, name = "top artists({}):".format(time_range))
            # so if user's dont listen to enough artists in the short term,
            # then less than 100 short term artists are returned
            # in which case ['items'] equals [] and so we must check for this
            # and just simply do nothing when it happens
            if resp_dict and resp_dict['total'] > 0 and len(resp_dict['items']) > 0:
                artists_df = self.extract_full_artist_from_json(resp_dict['items'])
                artists_df["top_artists_"+time_range] = True

                top_artists.append(artists_df)

        
        if len(top_artists) > 0:
            artists_df = pd.concat(top_artists)

            if 'id' in artists_df:
                current_ranking = 0
                rankings = []
                seen_id = set()
                for index, row in artists_df.iterrows():
                    if row['id'] not in seen_id:
                        current_ranking += 1
                        seen_id.add(row['id'])
                    rankings.append(current_ranking)

                artists_df["top_artists_" + time_range + "_ranking"] = rankings
                artists_df = artists_df[artists_df['id'].notnull()]

                self.artists_dataframes.append(artists_df)
        

    async def fetch_top_tracks(self, time_range):
        print('fetching top tracks... ', time_range)
        #self.track_columns.append("top_tracks_" + time_range)

        offsets = [0, 49]
        all_artists = []
        all_tracks = []
        
        for offset in offsets:
            URL = "https://api.spotify.com/v1/me/top/tracks?limit=50&offset="+str(offset)+"&time_range="+time_range
            resp_dict = await self.fetch_json_from_URL(URL = URL, name = "artists from top tracks({})".format(time_range))

            if resp_dict and resp_dict['total'] > 0 and len(resp_dict['items']) > 0:
                
                artists_df = json_normalize(data = resp_dict['items'], record_path=['artists'], meta=['id'], meta_prefix='track.')
                artists_df = artists_df[['id', 'name', 'track.id']]

                all_artists.append(artists_df)

                tracks_df = json_normalize(data = resp_dict['items'], record_path=['album', 'images'], meta=['id', 'name', 'uri'], meta_prefix='track.')
                tracks_df = self.cleanup_tracks_df(tracks_df)
                tracks_df["top_tracks_"+time_range] = True
                all_tracks.append(tracks_df)
        
        if len(all_artists) > 0:
            all_artists_df = pd.concat(all_artists)
            if 'id' in all_artists_df:
                all_artists_df = all_artists_df[all_artists_df['id'].notnull()]
                self.artists_dataframes.append(all_artists_df)

        if len(all_tracks) > 0:
            all_tracks_df = pd.concat(all_tracks)
            if 'id' in all_tracks_df:
                all_tracks_df = all_tracks_df[all_tracks_df['id'].notnull()]
                self.tracks_dataframes.append(all_tracks_df)



    async def fetch_followed_artists(self):
        print('fetching followed artists... ')
        self.artist_columns.append("followed_artist")

        next = "https://api.spotify.com/v1/me/following?type=artist&limit=50&offset=0"
        followed_artists = []

        while next:
            resp_dict = await self.fetch_json_from_URL(URL = next, name = "followed artists")

            if resp_dict and resp_dict['artists'] and resp_dict['artists']['total'] > 0 and len(resp_dict['artists']['items']) > 0:
                next = resp_dict['artists']['next']
                artists_df = self.extract_full_artist_from_json(resp_dict['artists']['items'])
                artists_df['followed_artist'] = True
                followed_artists.append(artists_df)
            else:
                break
            
        if len(followed_artists) > 0:
            followed_artists_df = pd.concat(followed_artists)
            if 'id' in followed_artists_df:
                followed_artists_df = followed_artists_df[followed_artists_df['id'].notnull()]
                self.artists_dataframes.append(followed_artists_df)


    async def fetch_saved_tracks(self):
        print('fetching saved tracks... ')
        #self.track_columns.append("saved_tracks")

        next = "https://api.spotify.com/v1/me/tracks?limit=50&offset=0"
        all_artists = []
        all_tracks = []
        
        while next:

            resp_dict = await self.fetch_json_from_URL(URL = next, name = "saved tracks")

            if resp_dict and resp_dict['total'] > 0 and len(resp_dict['items']) > 0:
                next = resp_dict['next']

                artists_df = json_normalize(data = resp_dict['items'], record_path=['track', 'artists'], meta=[['track', 'id']])
                artists_df = artists_df[['id', 'name', 'track.id']]
                all_artists.append(artists_df)

                tracks_df = json_normalize(data = resp_dict['items'], record_path=['track', 'album', 'images'], meta=[['track', 'name'], ['track', 'id'], ['track', 'uri']])
                tracks_df = self.cleanup_tracks_df(tracks_df)
                tracks_df["saved_tracks"] = True
                all_tracks.append(tracks_df)
            else:
                break


        if len(all_artists) > 0:
            all_artists_df = pd.concat(all_artists)
            if 'id' in all_artists_df:
                all_artists_df = all_artists_df[all_artists_df['id'].notnull()]
                self.artists_dataframes.append(all_artists_df)

        if len(all_tracks) > 0:
            all_tracks_df = pd.concat(all_tracks)
            if 'id' in all_tracks_df:
                all_tracks_df = all_tracks_df[all_tracks_df['id'].notnull()]
                self.tracks_dataframes.append(all_tracks_df)

    async def fetch_playlists(self):
        print('fetch_playlists...')
        playlists_all = []
        next = "https://api.spotify.com/v1/me/playlists?limit=50&offset=0"



        while next:
            resp_dict = await self.fetch_json_from_URL(URL = next, name = "playlists")

            if resp_dict and resp_dict['total'] > 0 and len(resp_dict['items']) > 0:
                next = resp_dict['next']

                playlists_full = json_normalize(resp_dict['items'])
                playlists = playlists_full[['id', 'owner.id']]

                if self.USER_PLAYLISTS_ONLY:
                    playlists = playlists[playlists['owner.id'] == self.user_id]

                playlists.drop('owner.id', axis=1, inplace=True)
                playlists_all.append(playlists)
            else:
                break

        if len(playlists_all) > 0:
            return pd.concat(playlists_all)

        return pd.DataFrame()

    async def get_all_playlists(self):
        playlists = await self.fetch_playlists()
        self.artist_columns.append("playlist")

        if playlists.empty or 'id' not in playlists:
            return

        tracks = []
        artists = []

        print('fetching', len(playlists), 'playlists...')

        tasks = [self.fetch_playlist(playlistID) for playlistID in playlists['id']]
        playlistDatas = await asyncio.gather(*tasks)

        for playlistData in playlistDatas:
            if not playlistData[0].empty:
                artists.append(playlistData[0])
            if not playlistData[1].empty:
                tracks.append(playlistData[1])

        self.artists_dataframes.append(pd.concat(artists))
        self.tracks_dataframes.append(pd.concat(tracks))


    async def fetch_playlist(self, ID):
        next = "https://api.spotify.com/v1/playlists/"+ID+"/tracks?limit=100&offset=0"
        all_artists = []
        all_tracks = []

        while next:
            resp_dict = await self.fetch_json_from_URL(URL = next, name = "tracks from playlist")

            if resp_dict and resp_dict['total'] > 0 and len(resp_dict['items']) > 0:

                next = resp_dict['next']
                
                artists_df = json_normalize(data = resp_dict['items'], record_path=['track', 'artists'], meta=[['track', 'id']])
                artists_df = artists_df[['id', 'name', 'track.id']]
                artists_df['playlist'] = True

                all_artists.append(artists_df)

                tracks_df = json_normalize(data = resp_dict['items'], record_path=['track', 'album', 'images'], meta=[['track', 'name'], ['track', 'id'], ['track', 'uri']])
                tracks_df = self.cleanup_tracks_df(tracks_df)
                tracks_df["playlist"] = True
                all_tracks.append(tracks_df)
            else:
                break

        all_artists_df = pd.DataFrame()
        all_tracks_df = pd.DataFrame()

        if len(all_artists) > 0:
            all_artists_df = pd.concat(all_artists)
            if 'id' in all_artists_df:
                all_artists_df = all_artists_df[all_artists_df['id'].notnull()]

        if len(all_tracks) > 0:
            all_tracks_df = pd.concat(all_tracks)
            if 'id' in all_tracks_df:
                all_tracks_df = all_tracks_df[all_tracks_df['id'].notnull()]
        
        return all_artists_df, all_tracks_df



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
        URL = "https://api.spotify.com/v1/artists"

        resp_dict = await self.fetch_json_from_URL(
            URL = URL, 
            params = [('ids', ",".join(IDs))],
            name = "full artist objects")
        
        if resp_dict and resp_dict['artists']:
            try:
                artist_df = self.extract_full_artist_from_json(resp_dict['artists'])
            except Exception as e:
                with open('errorArtists.json', 'w') as outfile:
                    json.dump(resp_dict['artists'], outfile)

            if artist_df.empty:
                return pd.DataFrame()

            if 'id' in artist_df:
                artist_df = artist_df[artist_df['id'].notnull()]
                return artist_df

        return pd.DataFrame()




    def split_into_N(self, _list, N):
        return [_list[i * N:(i + 1) * N] for i in range((len(_list) + N - 1) // N )]


    ''' json_data must be a JSON array of full artist objects. Returns a dataframe of all the objects with
        columns: id, name, genres, image, image_size'''
    def extract_full_artist_from_json(self, json_data):
        json_data_no_none = []
        for val in json_data:
            if val != None:
                json_data_no_none.append(val)


        artists_genres = json_normalize(data = json_data_no_none, record_path='genres', meta=['id', 'name', 'uri'])
        artists_images = json_normalize(data = json_data_no_none, record_path='images', meta=['id', 'name', 'uri'])

        if artists_genres.empty or artists_images.empty:
            print('artists_genres.empty', artists_genres.empty)
            print('artists_images.empty', artists_images.empty)
            return pd.DataFrame()

        artists_df = pd.merge(artists_genres, artists_images, how="outer")

        # filter out other sizes that we don't want

        # don't need height and width, only size since they are the same
        artists_df = artists_df.drop(['height'], axis=1)
        artists_df = artists_df.drop(['width'], axis=1)
        # genres columns defaults to '0' since we are extracting an array in the record_path ('genres'),
        # an array of strigs, not objects
        artists_df = artists_df.rename(columns={0: 'genres', 'url': 'image'})
        return artists_df

    '''
    track: {
        name
        id
        uri
        album: {
            images [{}]
        }
        artists: [{}]
    '''
    def cleanup_tracks_df(self, tracks_df):
        #   id      name        uri            height    width   url
        tracks_df = tracks_df.rename(columns={'track.id': 'id', 'track.name': 'name', 'track.uri': 'uri', 'url': 'image_url', 'width': 'image_size'})
        tracks_df = tracks_df.drop(['height'], axis=1)
        return tracks_df
        



    ''' fetch user id is implemented with requests library instead of asyncio '''
    def fetch_user_id(self):
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
    async def fetch_json_from_URL(self, URL, params = None, name = "", depth = 0):
        r = None
        async with aiohttp.ClientSession(raise_for_status=False) as session:
            try:
                r = await session.get(URL, params = params, headers = self.header)
            
                # can try again after waiting for a bit, not really an error
                if r.status == 429:
                    if depth > 3:
                        print('Error: recursion depth is 4')
                        return None
                    
                    if 'Retry-After' in r.headers:
                        sleepFor = int(r.headers['Retry-After']) + 1
                    else:
                        sleepFor = 5

                    print("status is 429, Too many requests... recursively trying again, in ", sleepFor, ', depth = ', depth)

                    await asyncio.sleep(sleepFor)
                    return await self.fetch_json_from_URL(URL, params, name, depth + 1)
                
                if r.status == 404:
                    # happens sometimes, try again
                    if depth > 3:
                        print('Error: recursion depth is 4')
                        return None
                    
                    print('404... recursively trying again, depth = ', depth)
                    return await self.fetch_json_from_URL(URL, params, name, depth + 1)

                if r.status != 200:
                    print('ERROR: spotify return status: ', r.status)
                    print(r.status, ".. recursively trying again, depth = ", depth)
                    await asyncio.sleep(1)
                    return await self.fetch_json_from_URL(URL, params, name, depth + 1)

                resp_dict = json.loads(await r.text())
                return resp_dict

            except aiohttp.ClientConnectorError as e:
                print('fetch_json_from_URL error')
                print('name: ', name)
                print('URL: ', URL)
                print('error msg: ', str(e))
                print('=========')
                return None