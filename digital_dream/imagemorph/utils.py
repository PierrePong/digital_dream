from google.cloud import storage
import os
import cv2


BUCKET_NAME = "m_digital_dream_bucket"


def save_to_gcp(bucket_path, local_path, rm_local=True):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME) # BUCKET NAME will be same everywhere
    blob = bucket.blob(bucket_path)
    blob.upload_from_filename(local_path)
    if rm_local:
        os.remove(local_path)


# def download_from_gcp():
#     client = storage.Client()
#     bucket = client.bucket(BUCKET_NAME) # BUCKET NAME will be same everywhere
#     blob = bucket.blob("data/train_1k.csv")
#     blob.download_to_filename("test")


def get_image_from_bucket(bucket_path, local_path, rm_local=True):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME) # BUCKET NAME will be same everywhere
    blob = bucket.blob(bucket_path)
    blob.download_to_filename(local_path)
    if rm_local:
        image = cv2.imread(local_path, cv2.IMREAD_COLOR)
        os.remove(local_path)
        return image
    # blob.download_as_bytes()