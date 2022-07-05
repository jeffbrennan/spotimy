import os
import spotipy
import pandas as pd
from spotipy.oauth2 import SpotifyOAuth
os.chdir(r'C:\Users\jeffb\Desktop\Life\personal-projects\spotify')

CREDENTIALS = pd.read_csv('backend/auth.csv').squeeze()
os.environ['SPOTIPY_CLIENT_ID'] = CREDENTIALS['id']
os.environ['SPOTIPY_CLIENT_SECRET'] = CREDENTIALS['secret']
os.environ['SPOTIPY_REDIRECT_URI'] = 'http://localhost:8080/'

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=["user-library-read", "user-read-recently-played"]))


def get_song_info(song):
    print(f"Adding to library: {song['track']['artists'][0]['name']} - {song['track']['name']}")

    try:
        timestamp = song['added_date']
    except KeyError: 
        timestamp = song['played_at']

    results = {
        'timestamp': timestamp,
        'artist': song['track']['artists'][0]['name'],
        'artist_id': song['track']['artists'][0]['id'],
        'album': song['track']['album']['name'],
        'track': song['track']['name'] ,
        'track_id': song['track']['id']
    }
    return results


def update_library(user):
    current_library = pd.read_csv(f'track_data/users/{user}/library.csv')
    DT_START = current_library['added_date'].max()

    song_len = sp.current_user_saved_tracks(limit=1, offset=0, market=None)['total']
    all_songs = []

    for song_index in list(range(0, song_len, 50)):
        if song_len - song_index < 50:
            max_songs = song_len - song_index
        else:
            max_songs = 50
        songs = sp.current_user_saved_tracks(limit=max_songs, offset=song_index, market=None)

        batch_results = [get_song_info(song) for song in songs['items'] if song['added_at'] > DT_START]
        
        if len(batch_results) == 0:
            print('No new songs')
            break
        else:
            all_songs.extend(batch_results)

    new_song_df = pd.DataFrame(all_songs)
    song_df = pd.concat([current_library, new_song_df])

    song_df.sort_values(by='added_date', ascending=False, inplace=True)
    song_df.to_csv(f'track_data/users/{user}/library.csv', index=False)


def get_listening_history(user):
    current_history = pd.read_csv(f'track_data/users/{user}/listening_history.csv')

    results = sp.current_user_recently_played()
    song_history = [get_song_info(result) for result in results['items']]

    new_history_df = pd.DataFrame(song_history)
    history_df = pd.concat([current_history, new_history_df])
    # history_df = new_history_df
    history_df.sort_values(by='timestamp', ascending=False, inplace=True)
    history_df.drop_duplicates(inplace=True)
    history_df.to_csv(f'track_data/users/{user}/listening_history.csv', index=False)


update_library('jeff')
get_listening_history('jeff')
 