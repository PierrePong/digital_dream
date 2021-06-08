import flickrapi
import requests
import urllib
import os
from dotenv import load_dotenv
from datetime import date, timedelta
# from PIL import Image

def flickr_downloader(hashtag='Marseille'):
    '''
    This function downloads photos with a defined hashtag
    from Flickr.com (1 user = 1 photo).
    Photos downloaded are from the previous day.
    '''
    # Get API keys from .env file
    load_dotenv()
    api_key = os.getenv('flickr_api_key')
    api_secret = os.getenv('flickr_api_secret')
    
    # Get today's and yesterday's dates
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
        
    # Forming a request to get unique user names for users having posts for the previous day
    url = 'https://www.flickr.com/services/rest/'
    params = dict(method='flickr.photos.search',
                api_key=api_key,
                text='marseille',
                min_upload_date=yesterday,
                max_upload_date=today,
                format='json',
                nojsoncallback=1
    )
    
    r = requests.get(url, params=params).json() # Receive a json file
    
    users = set() # Using a set to get only unique user names
    
    for item in r['photos']['photo']:
        users.add(item['owner']) # Get a set with only unique user names
    
    
    # Initialization and downloading the images
    flickr=flickrapi.FlickrAPI(api_key, api_secret, cache=True) 

    for user in users:
        # for list of arguments: https://www.flickr.com/services/api/flickr.photos.search.html
        photos = flickr.walk(text=hashtag, # searching for Marseille photos
                            user_id=user, #Photos from the set of users defined above
                            extras='url_c', # Don't know what it does!
                            per_page=500, # Number of photos to return per page. If this argument is omitted, it defaults to 100. The maximum allowed value is 500.
                            min_upload_date=yesterday,
                            max_upload_date=today,
        )

        for i, photo in enumerate(photos):
                url = photo.get('url_c')
                print(user, i, url)
                try:
                    urllib.request.urlretrieve(url, f'raw_data/flickr_{user}_{i}.jpg')
                except:
                    continue
                if i >= 0: # we are taking only 1 photo from each user
                    break

if __name__ == '__main__':
    flickr_downloader()