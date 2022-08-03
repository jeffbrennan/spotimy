import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd
import concurrent.futures

from yt_dlp import YoutubeDL

os.chdir('C:/Users/jeffb/Desktop/Life/personal-projects/spotify')
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

CLIENT_SECRET = "backend/youtube_secret.json"
CHANNEL_UPLOADS = 'UUt7fwAhXDy3oNFTAzF2o8Pw'
EXISTING_IDS = pd.read_csv('reviews/fantano.csv', sep='\t').squeeze()['vid_id'].to_list()

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


def download_caption(video_ids):
    ydl_opts = {
        "skip_download": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en"],
        'outtmpl': 'reviews/fantano_subs/%(id)s.%(ext)s',
        "subtitlesformat": "json3"
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download(video_ids)


def parse_item(item):
    video_id = item['snippet']['resourceId']['videoId']

    results = {'vid_id': video_id,
               'vid_published': item['snippet']['publishedAt'],
               'vid_title': item['snippet']['title']
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

    vid_ids = [i['snippet']['resourceId']['videoId'] for i in response['items']]
    new_ids = set(vid_ids) - set(EXISTING_IDS)
    
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

        all_ids = EXISTING_IDS.extend(all_vids['vid_id'].squeeze().to_list())
        existing_captions = [x.split('.')[0] for x in os.listdir('reviews/fantano_subs')]
        captions_to_dl = list(set(all_ids) - set(existing_captions))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(download_caption, captions_to_dl)


if __name__ == "__main__":
    main()
