import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import pandas as pd

CREDENTIALS = pd.read_csv('backend/auth.csv').squeeze()
os.environ['SPOTIPY_CLIENT_ID'] = CREDENTIALS['id']
os.environ['SPOTIPY_CLIENT_SECRET'] = CREDENTIALS['secret']
os.environ['SPOTIPY_REDIRECT_URI'] = 'http://localhost:8080/'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth())


def get_artist_genres(artist_ids):
    print(f'Getting genres for {len(artist_ids)} artists')
    artist_results = sp.artists(artist_ids)
    genres = [{i['id']: i['genres']} for i in artist_results['artists']]
    return genres


def get_track_analysis(track_ids):
    print(f'Analyzing {len(track_ids)} tracks')
    analysis = sp.audio_features(track_ids)
    return analysis


# TODO: transition csv files to local sql server
def write_df(track_analysis, artist_genres, user, listening_history, previous_analysis):
    track_analysis_flat = [x for xs in track_analysis for x in xs]
    genres_flat = [x for xs in artist_genres for x in xs]

    artist_ids_list = [x for xs in [list(i) for i in genres_flat] for x in xs]
    artist_genres_list = [x for xs in [i.values() for i in genres_flat] for x in xs]

    artist_genres_df = pd.DataFrame(list(zip(artist_ids_list, artist_genres_list)),
                                    columns=['artist_id', 'genres'])

    analysis_df = pd.DataFrame(track_analysis_flat)
    analysis_df.drop(['type', 'track_href', 'analysis_url', 'uri'], axis=1, inplace=True)

    unique_tracks = listening_history
    unique_tracks = unique_tracks.drop(['timestamp', 'artist', 'album', 'track'], axis=1)
    unique_tracks = unique_tracks.drop_duplicates()

    new_analysis = analysis_df.merge(unique_tracks, left_on='id', right_on='track_id', how='left')
    new_analysis = new_analysis.merge(artist_genres_df, left_on='artist_id', right_on='artist_id', how='left')

    new_analysis = new_analysis.reindex(
        columns=[
                    'artist_id', 'genres', 'track_id', 'danceability', 'energy', 'key', 'loudness', 'mode',
                    'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence',
                    'tempo', 'duration_ms', 'time_signature'
                ])

    all_analysis = pd.concat([previous_analysis, new_analysis])
    all_analysis.to_csv(f'track_data/users/{user}/listening_history_analysis.csv', index=False)

# TODO: make tracks unique
def analyze_listening_history(user):
    listening_history = pd.read_csv(f'track_data/users/{user}/listening_history.csv')
    previous_analysis = pd.read_csv(f'track_data/users/{user}/listening_history_analysis.csv')

    all_tracks = list(set(listening_history['track_id']) - set(previous_analysis['track_id']))
    track_chunks = [all_tracks[x:x+100] for x in range(0, len(all_tracks), 100)]

    all_artists = list(set(listening_history['artist_id']) - set(previous_analysis['artist_id']))
    artist_chunks = [all_artists[x:x+50] for x in range(0, len(all_artists), 50)]

    track_analysis = [get_track_analysis(i) for i in track_chunks]
    artist_genres = [get_artist_genres(i) for i in artist_chunks]

    if len(track_analysis) > 0:
        write_df(track_analysis, artist_genres, user, listening_history, previous_analysis)
    else:
        print('No new tracks to analyze')


USERS = ['jeff']
[analyze_listening_history(i) for i in USERS]
