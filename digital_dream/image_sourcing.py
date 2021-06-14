import requests
import urllib
import os
from dotenv import load_dotenv
from datetime import date, datetime, timedelta

# APIs
import flickrapi
import tweepy as tw


class Downloader():
    def __init__(self):
        pass


    def instagram_downloader(hashtag='marseille'):
        '''
        This function downloads photos with Marseille hashtag from Instagram.com
        '''
        # Get today's date and downloading time
        today = date.today().isoformat()
        d_time = datetime.now().strftime("%H-%M")
        
        # Create a new folder for fresh photos
        path = 'raw_data/Instagram'
        folder = f'Instagram_{today}_{d_time}'
        os.mkdir(f'{path}/{folder}')
        
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
            urllib.request.urlretrieve(url, f'{path}/{folder}/Instagram_{today}_{d_time}_{j}.jpg')


    def flickr_downloader(hashtag='marseille'):
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
        
        # Create a new folder for fresh photos
        path = 'raw_data/Flickr'
        folder = f'Flickr_{today}'
        os.mkdir(f'{path}/{folder}')
            
        # Forming a request to get unique user names for users having posts for the previous day
        url = 'https://www.flickr.com/services/rest/'
        params = dict(method='flickr.photos.search',
                    api_key=api_key,
                    text=hashtag,
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
                    try:
                        urllib.request.urlretrieve(url, f'{path}/{folder}/Flickr_{today}_{user}.jpg')
                    except:
                        continue
                    if i >= 0: # we are taking only 1 photo from each user
                        break


    def twitter_downloader(limit=1000):
        '''
        This function downloads photos with a defined hashtag
        from Twitter.com.
        Photos downloaded are from the previous day.
        '''
            
        # Get today's and yesterday's dates
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        # Create a new folder for fresh photos
        path = 'raw_data/Twitter'
        folder = f'Twitter_{today}'
        os.mkdir(f'{path}/{folder}')

        # Get API keys from .env file
        load_dotenv()

        CONSUMER_KEY = os.getenv('CONSUMER_KEY')
        CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
        ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
        ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')
    
        # identification
        auth = tw.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        api = tw.API(auth, wait_on_rate_limit=True)


        tweets = tw.Cursor(api.search,
                    q='#marseille',
                    lang="fr",
                    since=yesterday).items(limit)

        # create the list of url (one picture/url)
        list_url =[]
        
        for tweet in tweets:
            try:
                list_url.append(tweet.entities["media"][0]["media_url_https"])
            except:
                continue
        
        # exporting the pictures
        for i, url in enumerate(list_url):
            urllib.request.urlretrieve(url, f'{path}/{folder}/Twitter_{today}_{i}.jpg')

        
if __name__ == '__main__':
    Downloader()