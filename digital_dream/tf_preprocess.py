"""Tensorflow smart preprocessing for all our dataset"""
import tensorflow as tf
import tensorflow_datasets as tfds
from tensorboard.plugins import projector
import numpy as np
import shutil
import cv2
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
    directory, labels=None, label_mode=None,
    class_names=None, color_mode='rgb', batch_size=32, image_size=(256,
    256), shuffle=True, seed=None, validation_split=None, subset=None,
    interpolation='bilinear', follow_links=True, smart_resize=True
)
# we do an iteration with our generation and store it in image_batch
image_batch = next(iter(tfdf_img))

"""this function rescale the data to be used in tensorboard, it create also the file .tsv,
we have to passe 4 variable 2 time our dataset and 2 time our label (or an empty list if none)"""
def create_sprite(data):
    """
    Tile images into sprite image.
    Add any necessary padding
    """
    # For B&W or greyscale images
    if len(data.shape) == 3:
        data = np.tile(data[..., np.newaxis], (1, 1, 1, 3))
    n = int(np.ceil(np.sqrt(data.shape[0])))
    padding = ((0, n ** 2 - data.shape[0]), (0, 0), (0, 0), (0, 0))
    data = np.pad(data, padding, mode="constant", constant_values=0)
    # Tile images into sprite
    data = data.reshape((n, n) + data.shape[1:]).transpose((0, 2, 1, 3, 4))
    # print(data.shape) => (n, image_height, n, image_width, 3)
    data = data.reshape((n * data.shape[1], n * data.shape[3]) + data.shape[4:])
    # print(data.shape) => (n * image_height, n * image_width, 3)
    return data
def plot_to_projector(
    x,
    feature_vector,
    y,
    class_names,
    log_dir="default_log_dir",
    meta_file="metadata.tsv",
):
    assert x.ndim == 4  # (BATCH, H, W, C)
    # Remove log_dir if it exists
    if os.path.isdir(log_dir):
        shutil.rmtree(log_dir)
    # Create a new log_dir
    os.mkdir(log_dir)
    # Create Sprites file and write sprite into it
    SPRITES_FILE = os.path.join(log_dir, "sprites.png")
    sprite = create_sprite(x)
    cv2.imwrite(SPRITES_FILE, sprite)
    # Generate label names
#     labels = [class_names[y[i]] for i in range(int(y.shape[0]))]
#     with open(os.path.join(log_dir, meta_file), "w") as f:
#         for label in labels:
#             f.write("{}\n".format(label))
    with open(os.path.join(log_dir, meta_file), "w") as f:
            f.write("{}\n".format("unknown"))
    if feature_vector.ndim != 2:
        print(
            "NOTE: Feature vector is not of form (BATCH, FEATURES)"
            " reshaping to try and get it to this form!"
        )
        feature_vector = tf.reshape(feature_vector, [feature_vector.shape[0], -1])
        feature_vector = tf.Variable(feature_vector)
        checkpoint = tf.train.Checkpoint(embedding=feature_vector)
        checkpoint.save(os.path.join(log_dir, "embeddings.ckpt"))
        # Set up config
        config = projector.ProjectorConfig()
        embedding = config.embeddings.add()
        embedding.tensor_name = "embedding/.ATTRIBUTES/VARIABLE_VALUE"
        embedding.metadata_path = meta_file
        embedding.sprite.image_path = "sprites.png"
        embedding.sprite.single_image_dim.extend((x.shape[1], x.shape[2]))
        projector.visualize_embeddings(log_dir, config)

#We lauch our function on our dataset
#it will create a folder in the local google emplacement
plot_to_projector(image_batch,image_batch,[],[])

#We lauch our tensorboard in auto-reload with the file created
%load_ext tensorboard
%tensorboard --logdir ./default_log_dir