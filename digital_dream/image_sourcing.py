import requests
import urllib
import os
from dotenv import load_dotenv
from datetime import date, datetime

class Downloader():
    def __init__(self) -> None:
        pass

    def instagram_downloader(hashtag='marseille'):
        '''
        This function downloads photos with Marseille hashtag from Instagram.com
        '''
        # Get today's date and downloading time
        today = date.today().isoformat()
        d_time = datetime.now().strftime("%H_%M")
        
        # Get API keys from .env file
        load_dotenv()
        api_key = os.getenv('x-rapidapi-key')
        api_host = os.getenv('x-rapidapi-host')
        
        # Forming a request to get unique user names for users having posts for the previous day
        url = "https://instagram47.p.rapidapi.com/hashtag_post"
        
        headers = {
            'x-rapidapi-key' : api_key,
            'x-rapidapi-host' : api_host
        }
        
        url_list = set() # empty set to keep unique URLs leading to photos
        
        for i in range(10): # 10 requests per hour MAX (50 per day)!!!
            
            if i == 0:
                cursor = '' # empty for the first request
            else:
                cursor = r['body']['edge_hashtag_to_media']['page_info']['end_cursor'] # changing cursor to load next photos

            params = {
                "hashtag" : hashtag,
                "endcursor" : cursor
            }
            
            r = requests.get(url, headers=headers, params=params).json()
            
            # Loop to append all URLs from the request
            for item in r['body']['edge_hashtag_to_media']['edges']:
                url_list.add(item['node']['thumbnail_src'])

        # Download photos            
        for j, url in enumerate(url_list):
            urllib.request.urlretrieve(url, f'raw_data/Instagram/Instagram_{today}_{d_time}/Instagram_{today}_{d_time}_{j}.jpg')
        
if __name__ == '__main__':
    Downloader()