import os
import cv2
from datetime import date, datetime
import pandas as pd
from tensorflow.image import ssim
import numpy as np
import tensorflow as tf
from google.cloud import storage
from tempfile import TemporaryFile, NamedTemporaryFile
import matplotlib.pyplot as plt


BUCKET_NAME = 'm_digital_dream_bucket'
client = storage.Client()
bucket = client.bucket(BUCKET_NAME)


today = date.today().isoformat()
time = datetime.now().strftime("%H-%M")
IMAGE = '%d.jpg'


dir_1 = ('raw_data')
path = f'gs://{BUCKET_NAME}/Clusters/dossier_csv'
out_put_path = ('Clusters')
clusters = ['cluster_3_5_14_.csv',
            'cluster_pca_tsne_3_5_19.csv',
            'cluster_2021-06-15_14-08.csv',
            'cluster_2021-06-15_14-11.csv',
            'cluster_2021-06-15_14-13.csv',
            'cluster_2021-06-15_14-41.csv',
            'cluster_2021-06-15_14-48.csv',
            'cluster_2021-06-15_14-49.csv']

# def pour comparé les images cote à cote et retourne le SSIM 
def compare_images(imageA, imageB):
    im1 = tf.expand_dims(imageA, axis=0)
    im2 = tf.expand_dims(imageB, axis=0)
    im1_resize = tf.reshape(im1, (1, 512, 512, 3))
    im2_resize = tf.reshape(im2, (1, 512, 512, 3))
    s = ssim(im1_resize, im2_resize, max_val=255)
    return s 

# def pour lire les images d'origines en couleur 
def read_gcp(bucket, path):
    blob = bucket.blob(path)
    image = np.asarray(bytearray(blob.download_as_string()), dtype="uint8")
    imageBGR = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return imageBGR

# boucle pour comparé les noms d'images de clusters et les images d'origines 
# les csv de nom d'image des clusters
for i, cluster in enumerate(clusters): 
    df = pd.read_csv(f'{path}/{cluster}')
    #print(i, cluster)
    #print(len(df['filename'])-1)
    incre = 0
    # regarde image par image pour retrouvé les images d'origine
    for j in range(len(df['filename'])-1): 
        if incre < 19: 
            #print(os.path.join(dir_1, df['filename'][j]))
            pic1 = read_gcp(bucket ,os.path.join(dir_1, df['filename'][j])) # range la bonne image dans la var pic1 et rajoute le RGB
            pic1 = cv2.resize(pic1,(512,512)) # adapte l'image en 512, 512
            pic2 = read_gcp(bucket, os.path.join(dir_1, df['filename'][j+1]))
            pic2 = cv2.resize(pic2,(512,512))
            s = compare_images(pic1, pic2) # retourne le SSIM entre les 2 images
            #print(j)
            #print(s)
            if s < 0.9: # si SSIM < 0.9 alors les 2 images sont pas identique donc rajout des 2 images
                name = IMAGE % incre
                with NamedTemporaryFile(suffix='.jpg') as gcs_image:
                    # recupére le nom de l'image et le lien dans gcs_image
                    cv2.imwrite(gcs_image.name, pic1)
                    gcs_image.seek(0)
                    # créer un dossier pour les images du cluster i
                    blob = bucket.blob(f'{out_put_path}/cluster_{today}_{time}_{i}/{name}')
                    # upload le gcs_image
                    blob.upload_from_file(gcs_image)
                incre = incre+1
                name = IMAGE % incre
                with NamedTemporaryFile(suffix='.jpg') as gcs_image:
                    cv2.imwrite(gcs_image.name, pic2)
                    gcs_image.seek(0)
                    blob = bucket.blob(f'{out_put_path}/cluster_{today}_{time}_{i}/{name}')
                    blob.upload_from_file(gcs_image)
            else: # si SSIM > 0.9 alors les 2 images sont identique on ne récupére que la 2éme image
                name = IMAGE % incre
                with NamedTemporaryFile(suffix='.jpg') as gcs_image:
                    cv2.imwrite(gcs_image.name, pic2)
                    gcs_image.seek(0)
                    blob = bucket.blob(f'{out_put_path}/cluster_{today}_{time}_{i}/{name}')
                    blob.upload_from_file(gcs_image)
                incre = incre-1