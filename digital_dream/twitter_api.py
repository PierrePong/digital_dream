import urllib
import os
from dotenv import load_dotenv
from datetime import date, timedelta
import tweepy as tw



def twitter_downloader(limit=1000):
    '''
    This function downloads photos with a defined hashtag
    from Twitter.com.
    Photos downloaded are from the previous day.
    '''
        
    # Get today's and yesterday's dates
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

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
        print(tweet)
        try:
            list_url.append(tweet.entities["media"][0]["media_url_https"])
            
        except:
            pass
    
    # exporting the pictures
    for i, url in enumerate(list_url):
        urllib.request.urlretrieve(url, f'raw_data/twitter{i}.jpg')
        
        
if __name__ == '__main__':
    twitter_downloader(limit=5)