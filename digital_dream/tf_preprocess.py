"""Tensorflow smart preprocessing for all our dataset"""
import tensorflow as tf
import os

"""the importation from google drive is manual
you have to run this part in collab separately, connect to google and then retrieve the code
maybe later we will package the preprocessing code and store the data in gcp 
so that it will be automatic"""
from google.colab import drive
drive.mount('/content/drive', force_remount=True)

#we retrieve our files folders
directory = '/content/drive/MyDrive/Raw_data/'
for root, subdirectories, files in os.walk(directory):
    for subdirectory in subdirectories:
        img_folder=os.path.join(root, subdirectory)
        print(img_folder)

#we preprocess our data with smart_resize of tensorflow
"""all data are in only one batch with no train/validation split but it can be changed,
also size is 256x256"""
tfdf_img= tf.keras.preprocessing.image_dataset_from_directory(
    img_folders, labels=None, label_mode=None,
    class_names=None, color_mode='rgb', batch_size=32, image_size=(256,
    256), shuffle=True, seed=None, validation_split=None, subset=None,
    interpolation='bilinear', follow_links=True, smart_resize=True
)
