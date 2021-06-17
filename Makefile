# ----------------------------------
#          INSTALL & TEST
# ----------------------------------
install_requirements:
	@pip install -r requirements.txt

check_code:
	@flake8 scripts/* digital_dream/*.py

black:
	@black scripts/* digital_dream/*.py

test:
	@coverage run -m pytest tests/*.py
	@coverage report -m --omit="${VIRTUAL_ENV}/lib/python*"

ftest:
	@Write me

clean:
	@rm -f */version.txt
	@rm -f .coverage
	@rm -fr */__pycache__ */*.pyc __pycache__
	@rm -fr build dist
	@rm -fr digital_dream-*.dist-info
	@rm -fr digital_dream.egg-info

install:
	@pip install . -U

all: clean install test black check_code

count_lines:
	@find ./ -name '*.py' -exec  wc -l {} \; | sort -n| awk \
        '{printf "%4s %s\n", $$1, $$2}{s+=$$0}END{print s}'
	@echo ''
	@find ./scripts -name '*-*' -exec  wc -l {} \; | sort -n| awk \
		        '{printf "%4s %s\n", $$1, $$2}{s+=$$0}END{print s}'
	@echo ''
	@find ./tests -name '*.py' -exec  wc -l {} \; | sort -n| awk \
        '{printf "%4s %s\n", $$1, $$2}{s+=$$0}END{print s}'
	@echo ''

# ----------------------------------
#      UPLOAD PACKAGE TO PYPI
# ----------------------------------
PYPI_USERNAME=<AUTHOR>
build:
	@python setup.py sdist bdist_wheel

pypi_test:
	@twine upload -r testpypi dist/* -u $(PYPI_USERNAME)

pypi:
	@twine upload dist/* -u $(PYPI_USERNAME)

# ----------------------------------
#      UPLOAD PACKAGE TO GCP
# ----------------------------------
BUCKET_NAME = "m_digital_dream_bucket"
PROJECT_ID = "marseille-digital-dream"
REGION='europe-west1'

#mounted_drive:
#if data are in the drive it should be open in a collab notebook
#	from google.colab import drive
#	drive.mount('/content/drive', force_remount=True)

set_project:
	@gcloud config set project ${PROJECT_ID}

#create_bucket:
#here the bucket is already created in GCP
#	@gsutil mb -l ${REGION} -p ${PROJECT_ID} gs://${BUCKET_NAME}
# path to the file to upload to GCP (the path to the file should be absolute or should match the directory where the make command is ran)
# replace with your local path to the `train_1k.csv` and make sure to put the path between quotes
#LOCAL_PATH="/content/drive/My\ Drive/Raw_data"


# bucket directory in which to store the uploaded file (`data` is an arbitrary name that we choose to use)
#BUCKET_FOLDER=raw_data

# name for the uploaded file inside of the bucket (we choose not to rename the file that we upload)
#BUCKET_FILE_NAME=$(shell basename ${LOCAL_PATH})

#indentification may be needed to write in the gcp
#!gcloud auth login

upload_data:

#store a folder and all files inside :
#/!\ in the code below the star is at the end of the folder so it will copy the folder name 
#and all the file inside no need to put the folder name at the end
	@gsutil -m cp -r /content/drive/My\ Drive/Clusters/cluster_2021-06-15_14-15_1* gs://m_digital_dream_bucket/Clusters/
# store a file
	@gsutil -m cp ${LOCAL_PATH}/* gs://${BUCKET_NAME}/${BUCKET_FOLDER}/${BUCKET_FILE_NAME}

#################################################################
# for morph

install_local:
	pip install -e .

# bucket
BUCKET_NAME=m_digital_dream_bucket

# training folder, where package will be saved on bucket
BUCKET_TRAINING_FOLDER=trainings

# job name
JOB_NAME=morph_training_$(shell date +'%Y%m%d_%H%M%S')

# package name
PACKAGE_NAME=imagemorph

# Python job name, the python file to run for training
FILENAME=morph

#
PYTHON_VERSION=3.7
RUNTIME_VERSION=2.3

# Might be changed for US
REGION=europe-west1

# TEST 1:  sur 3 images max sans upload GCP
# TEST 2:  sur 3 images max avec upload GCP
test_training:
	python -m ${PACKAGE_NAME}.${FILENAME}



# Après TEST, submit sur GCP avec upload
gcp_submit_training:
	gcloud ai-platform jobs submit training ${JOB_NAME} \
		--job-dir gs://${BUCKET_NAME}/${BUCKET_TRAINING_FOLDER} \
		--package-path ${PACKAGE_NAME} \
		--module-name ${PACKAGE_NAME}.${FILENAME} \
		--python-version=${PYTHON_VERSION} \
		--runtime-version=${RUNTIME_VERSION} \
		--region ${REGION} \
		--stream-logs
