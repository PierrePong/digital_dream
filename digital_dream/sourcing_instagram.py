import requests
import urllib
import os
from dotenv import load_dotenv
from datetime import date
import time

def instagram_downloader(hashtag='marseille'):
    '''
    This function downloads photos with #marseille hashtag from Instagram.com
    '''
    # Getting today's date
    today = date.today().isoformat()
    
    # Creating a new folder for fresh photos
    path = 'raw_data/Instagram'
    folder = f'Instagram_{today}'
    
    try: # in case the folder already exists
        os.mkdir(f'{path}/{folder}')
    except:
        pass
    
    # Get API keys from .env file
    load_dotenv()
    api_key = os.getenv('x-rapidapi-key')
    api_host = os.getenv('x-rapidapi-host')
    
    # Forming a request to get unique user names for users having posts for the previous day
    print('Instagram API is active')
    
    url = "https://instagram47.p.rapidapi.com/hashtag_post"
    
    headers = {
        'x-rapidapi-key' : api_key,
        'x-rapidapi-host' : api_host
    }
    
    # Loading a black list with user_id to ignore (rubish posts only)
    black_list = open('digital_dream/black_list.txt', "r").read().split('\n')
    
    # Signal to exit the while loop
    error_message = [{'message': 'You have exceeded the rate limit per hour for your plan, BASIC, by the API provider'},
                     {'message': 'You have exceeded the DAILY quota for Requests on your current plan, BASIC. Upgrade your plan at https://rapidapi.com/Prasadbro/api/instagram47'}]
    
    r = 0 # Just to start with an empty cursor and to lunch the while loop
    
    while r not in error_message: # 10 requests per hour MAX (50 per day)!!!
        
        print('Proceeding request')
        
        if r == 0:
            cursor = '' # empty for the first request
        else:
            try:
                cursor = r['body']['edge_hashtag_to_media']['page_info']['end_cursor'] # changing cursor to load next photos
            except:
                print('There are some troubles with the API. See you in a minute! Sleepy now (-_-)')
                time.sleep(60) # Wait for 60 seconds before repeating the request

        params = {
            "hashtag" : hashtag,
            "endcursor" : cursor
        }
        
        try:
            r = requests.get(url, headers=headers, params=params).json()
            
            # Loop to download all images from the request
            for j, item in enumerate(r['body']['edge_hashtag_to_media']['edges']):
                if (item['node']['owner']['id'] not in black_list) and (item['node']['is_video']) == False:
                    image_url = item['node']['thumbnail_src']
                    user_id = item['node']['owner']['id']
                    print(f'Downloading photo #{j}')
                    urllib.request.urlretrieve(image_url, f'{path}/{folder}/Instagram_{today}_{user_id}.jpg')
                
        except:
            print(r)
            continue

    print('Instagram API is over')
    
if __name__ == '__main__':
    instagram_downloader()
