# -*- coding: utf-8 -*-

# Sample Python code for youtube.channels.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python

import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd

os.chdir('C:/Users/jeffb/Desktop/Life/personal-projects/spotify')
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
# CHANNEL_ID = 'UCt7fwAhXDy3oNFTAzF2o8Pw'
CLIENT_SECRET = "backend/youtube_secret.json"
CHANNEL_UPLOADS = 'UUt7fwAhXDy3oNFTAzF2o8Pw'
EXISTING_IDS = pd.read_csv('reviews/fantano.tsv', sep='\t').squeeze()['vid_id']


def build_client():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"


    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET, scopes)
    credentials = flow.run_console()
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    return youtube


def parse_item(item): 
    results = {'vid_id': item['id'],
               'vid_published': item['snippet']['publishedAt'],
               'vid_title': item['snippet']['title'],
               'vid_description': item['snippet']['description']
               }
    return results


def get_vids(youtube, next_page=''): 
    request = youtube.playlistItems().list(
        part="id,snippet",
        maxResults=50,
        playlistId="UUt7fwAhXDy3oNFTAzF2o8Pw",
        pageToken=next_page

    )
    response = request.execute()

    vid_ids = [i['id'] for i in response['items']]
    new_ids = set(vid_ids) - set(EXISTING_IDS)
    

    # TODO: get positions of actual new ids and run using that instead
    if len(new_ids) > 0: 
        output = {'NextPageToken': response['nextPageToken'],
                  'items': response['items'][0:len(new_ids)]
                  }
    else: 
        print('No new vids!')
        output = None
        
    return output


def main():
    results = []
    
    youtube = build_client()
    response = get_vids(youtube)
    
    if response is not None:
        results.extend([parse_item(i) for i in response['items']])
        while True:
            try:
                print(response['NextPageToken'])
                response = get_vids(youtube, response['NextPageToken'])
                results.extend([parse_item(i) for i in response['items']])
            
            except KeyError:
                print('All videos parsed')
                break

    all_vids = pd.DataFrame(results)
    all_vids.to_csv('reviews/fantano.csv', sep='\t', mode='a', index=False, header=False)
    # all_vids.to_csv('reviews/fantano.csv', sep='\t', index=False)


if __name__ == "__main__":
    main()