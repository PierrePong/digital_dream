import requests
import urllib
import os
from dotenv import load_dotenv
from datetime import date

def instagram_downloader(hashtag='marseille'):
    '''
    This function downloads photos with Marseille hashtag from Instagram.com
    '''
    # Get today's date
    today = date.today().isoformat()
    
    # Get API keys from .env file
    load_dotenv()
    api_key = os.getenv('x-rapidapi-key')
    api_host = os.getenv('x-rapidapi-host')
    
    # Forming a request to get unique user names for users having posts for the previous day
    url = "https://instagram47.p.rapidapi.com/hashtag_post"
    
    cursor = '' # empty for the first request
    
    params = {
        "hashtag" : hashtag,
        "endcursor" : cursor
    }
    
    headers = {
        'x-rapidapi-key' : api_key,
        'x-rapidapi-host' : api_host
    }
    
    url_list = set() # empty set to keep unique URLs leading to photos
    
    for i in range(10): # 10 requests per hour MAX (50 per day)!!!
        try:
            r = requests.get(url, headers=headers, params=params).json()
            cursor = r['body']['edge_hashtag_to_media']['page_info']['end_cursor'] # changing cursor to load next photos
        
            # Loop to append all URLs from the request
            for item in r['body']['edge_hashtag_to_media']['edges']:
                url_list.add(item['node']['thumbnail_src'])
        except:
            continue

    # Download photos            
    for i, url in enumerate(url_list):
            urllib.request.urlretrieve(url, f'raw_data/instagram_{today}_{i}.jpg')
        
if __name__ == '__main__':
    instagram_downloader()