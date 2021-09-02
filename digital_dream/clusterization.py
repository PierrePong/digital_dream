from datetime import date
import os
import numpy as np
import pandas as pd
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
from digital_dream.utils import k_mean_distance
import random
import shutil

def clustering():
    '''Converts all images in the current dirrectory
    into 1 numpy array. Images are croped to a desired size and
    the RGB values are normalized between 0 and 1'''
    # Getting today's date
    today = date.today().isoformat()

    # Creating a new folder for a cluster
    path = 'raw_data/Clusters'
    folder = f'Cluster_{today}'

    try: # in case the folder already exists
        os.mkdir(f'{path}/{folder}')
    except:
        pass

    img_dir = f'raw_data/Instagram/Instagram_{today}'
    cluster_dir = f'{path}/{folder}'

    # Getting list of all files in the directory + counting the files
    files = os.listdir(img_dir)
    number_files = len(files)

    # Image size used for clustering
    image_size = (128, 128) 

    # Converting each image to an array + appending the array to a list
    img_array = np.empty((number_files, image_size[0], image_size[1], 3))
    filenames = [] # To keep track of filenames for further images extraction from clusters

    for i, img in enumerate(files):
        filenames.append(img)
        im = load_img(os.path.join(img_dir,img), target_size=(image_size)) # loading image by image
        im = img_to_array(im)
        img_array[i] = im
        
    # Normalization and flattening
    array_norm = (img_array /255).reshape(img_array.shape[0], image_size[0]*image_size[1]*3)

    '''Before using TSNE we need to drastically reduce the number of features (below 50).
    That's why we use first series of PCAs and only then TSNEs'''
    # Bloc of 3 PCAs with progressive reduction of number of features
    pca_1 = PCA(n_components=200)
    pca_data_1 = pca_1.fit_transform(array_norm)

    pca_2 = PCA(n_components=100)
    pca_data_2 = pca_2.fit_transform(pca_data_1)

    pca_3 = PCA(n_components=30)
    pca_data_3 = pca_3.fit_transform(pca_data_2)

    # Bloc of 2 TSNEs
    tsne_1 = TSNE(n_components=3)
    tsne_data_1 = tsne_1.fit_transform(pca_data_3)

    tsne_2 = TSNE(n_components=2)
    tsne_data_2 = tsne_2.fit_transform(tsne_data_1)

    # Clustering with KMeans
    km = KMeans(n_clusters=round(tsne_data_2.shape[0] / 15)) # Division by 15 to get clusters with ~10-20 images in each
    kmeans_data = km.fit_predict(tsne_data_2)
    kmeans_df = pd.DataFrame(kmeans_data, columns = ['labels'])
    kmeans_df['filename'] = [item for item in filenames]

    '''Getting the most homogenious cluster based on the median value of distances to the cluster's center'''
    centroids = km.cluster_centers_ # x, y coordinates of the center of every cluster
    distances = [] # list of lists; distance from the cluster's center to every point in the cluster

    for i, (cx, cy) in enumerate(centroids):
        mean_distance = k_mean_distance(tsne_data_2, cx, cy, i, kmeans_data) # function from utils.py
        distances.append(mean_distance)

    min_distance = np.median(distances[0]) 
    cluster_number = 0

    for i, item in enumerate(distances):
        if (np.median(item) < min_distance) and np.median(item) != 0:
            min_distance = np.median(item)
            cluster_number = i

    # Saving 6 random images from the best cluster to a local folder
    cluster = list(kmeans_df[kmeans_df['labels'] == cluster_number]['filename'])

    for i in range(7): # take only 6 different images for Instagram post
        random_element = random.choice(cluster)
        shutil.copy(f'{img_dir}/{random_element}',cluster_dir)
        shutil.move(f'{cluster_dir}/{random_element}', f'{cluster_dir}/{i}.jpg') # A way to rename a file
        if i == 0:
            shutil.copy(f'{img_dir}/{random_element}',cluster_dir)
            shutil.move(f'{cluster_dir}/{random_element}', f'{cluster_dir}/7.jpg') # Create a duplicate of the first image to make a loop video
        cluster.remove(random_element)

if __name__ == '__main__':
    clustering()
    