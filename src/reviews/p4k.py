
# import requests
import pandas as pd
import re
# from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.error import HTTPError
from lxml import etree
from numpy import random
from time import sleep
import unidecode


# https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]
 

def scrape_score(album_dict, i):
    artist = album_dict['artist'][i]
    album = album_dict['album'][i]

    print(f'\n[{i:04d}] {artist} - {album}')
    print('PARSING...')
    artist_album = (artist + ' ' + album).strip().replace(' ', '-').lower()
    artist_album_clean = unidecode.unidecode(artist_album)

    for old, new in STR_REPLACEMENTS:
        artist_album_clean = re.sub(old, new, artist_album_clean)

    request_url = f'https://pitchfork.com/reviews/albums/{artist_album_clean}/'
    sleep(random.uniform(1, 2))

    try:
        response = urlopen(request_url)
        htmlparser = etree.HTMLParser()
        tree = etree.parse(response, htmlparser)

        album_review_date_raw = tree.xpath(DATE_XPATH)
        if len(album_review_date_raw) == 0: 
            try: 
                album_review_date = tree.xpath(DATE_XPATH2)[0].text
            except IndexError:
                album_review_date = None
        else: 
            album_review_date = tree.xpath(DATE_XPATH)[0].text

        bnm_check = tree.xpath(BNM_XPATH)
        if len(bnm_check) == 0:
            album_BNM = 0
            album_score = float(tree.xpath(SCORE_XPATH_NO_BNM)[0].text)
        else:
            album_BNM = 1
            album_score = float(tree.xpath(SCORE_XPATH_BNM)[0].text)

    except HTTPError or IndexError:
        print(f'PARSE ERROR: {request_url}')
        album_score = None
        album_BNM = None
        album_review_date = None
        
    output = {'artist': artist,
              'album': album,
              'score': album_score,
              'bnm': album_BNM,
              'review_date': album_review_date,
              'review_url': request_url
              }

    return(output)


def get_scores(user): 
    user_library = pd.read_csv(f'{BASE_PATH}/users/{user}/library.csv')
    p4k = pd.read_csv(f'{BASE_PATH}/p4k.csv')

    unique_albums = user_library.drop_duplicates(subset=['artist', 'album'])[['artist', 'album']]
    unique_p4k = p4k[['artist', 'album']]

    new_albums = unique_albums.append(unique_p4k[['artist', 'album']]).drop_duplicates(keep=False)
    album_dict = new_albums.reset_index().to_dict()

    new_albums_len = len(album_dict['album'])
    chunks = list(divide_chunks(range(0, new_albums_len), 5))

    # chunk to write every 10 searches
    if new_albums_len > 1:
        for chunk in chunks:
            scores = [scrape_score(album_dict, i) for i in chunk]
            scores_df = pd.DataFrame(scores)
            scores_df.to_csv(f'{BASE_PATH}/p4k.csv', mode='a', index=False, header=False)
    else:
        print('No new albums!')


BNM_XPATH = '/html/body/div[1]/div/main/article/div[1]/header/div[1]/div[2]/div/div[2]/div/div[1]/svg/g'
SCORE_XPATH_BNM = '/html/body/div[1]/div/main/article/div[1]/header/div[1]/div[2]/div/div[2]/div/div[2]/p'
SCORE_XPATH_NO_BNM = '/html/body/div[1]/div/main/article/div[1]/header/div[1]/div[2]/div/div[2]/div/div/p'
DATE_XPATH = '/html/body/div[1]/div/main/article/div[1]/header/div[3]/div/div/div/ul/li[3]/div/p[2]'
DATE_XPATH2 = '/html/body/div[1]/div/main/article/div[1]/header/div[3]/div/div/div/ul/li[2]/div/p[2]'
BASE_PATH = 'C:/Users/jeffb/Desktop/Life/personal-projects/spotify/track_data'

STR_REPLACEMENTS = [
    ('[^0-9a-zA-Z|-]+', ''),
    ('-$|^-', ''),
    ('--', '-'),
]

get_scores('jeff')