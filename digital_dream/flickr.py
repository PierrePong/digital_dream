import flickrapi
import urllib
# from PIL import Image
# from tqdm import tqdm

# Flickr api access key 
# To change with our own keys?

api_key = 'c6a2c45591d4973ff525042472446ca2'
api_secret = '202ffe6f387ce29b'

def flickr_downloader(hashtag='Marseille', n_photos = 100):
    '''
    This function downloads n_photos with a defined hashtag from Flickr.com
    '''
    flickr=flickrapi.FlickrAPI(api_key, api_secret, cache=True)

    # for list of arguments: https://www.flickr.com/services/api/flickr.photos.search.html
    photos = flickr.walk(text=hashtag, # searching for Marseille photos
                        tag_mode='all', # Either 'any' for an OR combination of tags, or 'all' for an AND combination. Defaults to 'any' if not specified.
                        tags=hashtag, # we gonna download pictures with this hashtag
                        extras='url_c',
                        per_page=500, # Number of photos to return per page. If this argument is omitted, it defaults to 100. The maximum allowed value is 500.
                        #  min_upload_date='2021-06-01',
                        #  max_upload_date='2021-06-02',
                        sort='date-posted-desc') # The order in which to sort returned photos.

    for i, photo in enumerate(photos):
            print(i)
            url = photo.get('url_c')
            try:
                urllib.request.urlretrieve(url, f'raw_data/{i}.jpg')
            except:
                continue
            if i >= n_photos:
                break

    # # Resize the image and overwrite it
    # image = Image.open('00001.jpg') 
    # image = image.resize((256, 256), Image.ANTIALIAS)
    # image.save('00002.jpg')

if __name__ == '__main__':
    flickr_downloader()