import os
import boto3
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

'''
To test set environment variable `export FLASK_APP=lumo_api` and run `flask run`
'''
app = Flask(__name__)
cors = CORS(app)

DEFAULT_PREDICTION_DIR='goes-predictions/'
GT_DIR='goes-ground-truths/'
EX_PREDICTIONS_DIR = 'examples/predictions/'
MRMS_PREDICTION_DIR='mrms-predictions/'
MRMS_GT_DIR='mrms-ground-truths/'
BUCKET='lumo-app'
URL_PREFIX = f"https://{BUCKET}.s3.amazonaws.com/"

load_dotenv()  # Uses .env file with access keys
s3_client = boto3.client(
  service_name='s3',
  aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
  aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

'''
Responds with a json containing every other item in the predictions directory
'''
@app.route('/predictions', methods=['GET'])
def return_prediction_urls():
  path = DEFAULT_PREDICTION_DIR + request.args.get('band', 'C07') + '/'
  s3_response = s3_client.list_objects_v2(Bucket=BUCKET, Prefix=path)
  contents = s3_response.get("Contents")
  if not contents:
    return "Path does not exist", 404
  predictions = []  # [oldest...newest]
  toggle = True  # Returns every other image (10 minute timestamps)
  timestamp = None

  for index, element in enumerate(contents):
    # print(element.get('Key'))
    # print(format(index, '02'))
    filename = element.get('Key').split('/')[-1]

    if not filename: 
      # Skip directories
      continue

    if toggle:
      if not timestamp:
        try:
          timestamp = datetime.strptime(filename[0:-4].split('_')[-1], "%Y-%m-%d-%H%M")
        except ValueError:
          return "Date and time in filename formatted incorrectly", 400

      timestamp = timestamp + timedelta(minutes=10)
      cloud_name = s3_client.list_objects_v2(Bucket=BUCKET, Prefix="cloud-cover/{0:02}".format(index)).get("Contents")[-1].get('Key')
      cloud = s3_client.get_object(Bucket=BUCKET, Key=cloud_name)
      s3_file = {
          "filename": filename,
          "url": URL_PREFIX + element.get('Key'),
          "last_modified": element.get("LastModified").strftime('%Y-%m-%dT%H:%M:%SZ'),
          # Change timestamp to date parsed from filename
          "timestamp": timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
          "cloud_str": json.loads(cloud['Body'].read()).get("cloud_str")
        }

      for i, p in enumerate(predictions):
        # inserts if timestamp is older than p['timestamp']
        if timestamp < datetime.strptime(p['timestamp'], '%Y-%m-%dT%H:%M:%SZ'):
          predictions.insert(i, s3_file)
          break
      predictions.append(s3_file)

    toggle = not toggle

  return jsonify(predictions)

'''
Responds with a json containing the 9 most recent ground truth images
'''
@app.route('/gt', methods=['GET'])
def return_ground_truths():
  path = GT_DIR + request.args.get('band', 'C07') + '/'
  s3_response = s3_client.list_objects_v2(Bucket=BUCKET, Prefix=path)
  contents = s3_response.get("Contents")
  if not contents:
    return "Path does not exist", 404
  gts = [] # [oldest...newest]

  for element in contents:
    filename = element.get('Key').split('/')[-1]

    if not filename:
      # Skip directories
      continue

    try:
      timestamp = datetime.strptime(filename.split('-goes')[0], "%Y-%m-%d-%H%M")
    except ValueError:
      timestamp = datetime(2000, 1, 1)  # Older than any data

    s3_file = {
        "filename": filename,
        "url": URL_PREFIX + element.get('Key'),
        "last_modified": element.get("LastModified").strftime('%Y-%m-%dT%H:%M:%SZ'),
        # Change timestamp to date parsed from filename
        "timestamp": timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
      }

    for i, gt in enumerate(gts):
      # if timestamp is older than gt['timestamp']
      if timestamp < datetime.strptime(gt['timestamp'], '%Y-%m-%dT%H:%M:%SZ'):
        gts.insert(i, s3_file)
        break
    gts.append(s3_file)

  return jsonify(gts[-9:])  

'''
Responds with a json containing every item in the mrms predictions directory
'''
@app.route('/mrms-predictions', methods=['GET'])
def return_mrmrs_prediction_urls():
  path = MRMS_PREDICTION_DIR + "mrms_{}h/".format(request.args.get('type', '24'))
  s3_response = s3_client.list_objects_v2(Bucket=BUCKET, Prefix=path + '0')
  contents = s3_response.get("Contents")
  if not contents:
    return "Path does not exist", 404
  predictions = []  # [oldest...newest]
  timestamp = None
  rainfall = s3_client.get_object(Bucket=BUCKET, Key=path + "rainFallData")
  rain_json = json.loads(rainfall['Body'].read())
  for index, element in enumerate(contents):
    filename = element.get('Key').split('/')[-1]

    if not filename:
      # Skip directories
      continue

    if not timestamp:
      try:
        timestamp = datetime.strptime(filename.split('_')[-1], "%Y-%m-%d-%H%M")
      except ValueError:
        return "Date and time in filename formatted incorrectly", 400

    timestamp = timestamp + timedelta(minutes=10)

    s3_file = {
        "filename": filename,
        "url": URL_PREFIX + element.get('Key'),
        "last_modified": element.get("LastModified").strftime('%Y-%m-%dT%H:%M:%SZ'),
        # Change timestamp to date parsed from filename
        "timestamp": timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "rainfall": rain_json.get(str(index))
      }

    for i, p in enumerate(predictions):
      # inserts if timestamp is older than p['timestamp']
      if timestamp < datetime.strptime(p['timestamp'], '%Y-%m-%dT%H:%M:%SZ'):
        predictions.insert(i, s3_file)
        break
    predictions.append(s3_file)

  return jsonify(predictions)

@app.route('/mrms-gt', methods=['GET'])
def return_mrms_gt_urls():
  path = MRMS_GT_DIR
  s3_response = s3_client.list_objects_v2(Bucket=BUCKET, Prefix=path)
  contents = s3_response.get("Contents")
  if not contents:
    return "Path does not exist", 404
  predictions = []  # [oldest...newest]
  timestamp = None

  for element in contents:
    filename = element.get('Key').split('/')[-1]

    if not filename:
      # Skip directories
      continue


    if not timestamp:
      try:
        timestamp = datetime.strptime(filename.split('_')[-1], "%Y-%m-%d-%H%M")
      except ValueError:
        return "Date and time in filename formatted incorrectly", 400

    timestamp = timestamp + timedelta(minutes=10)

    s3_file = {
        "filename": filename,
        "url": URL_PREFIX + element.get('Key'),
        "last_modified": element.get("LastModified").strftime('%Y-%m-%dT%H:%M:%SZ'),
        # Change timestamp to date parsed from filename
        "timestamp": timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
      }

    for i, p in enumerate(predictions):
      # inserts if timestamp is older than p['timestamp']
      if timestamp < datetime.strptime(p['timestamp'], '%Y-%m-%dT%H:%M:%SZ'):
        predictions.insert(i, s3_file)
        break
    predictions.append(s3_file)

  return jsonify(predictions)

'''
General item fetcher
'''
@app.route('/fetch', methods=['GET'])
def return_items():
  path = request.args.get('path', 'examples/ground-truths/C07/')
  s3_response = s3_client.list_objects_v2(Bucket=BUCKET, Prefix=path)
  contents = s3_response.get("Contents")
  if not contents:
    return "Path does not exist", 404
  items = []

  for element in contents:
    filename = element.get('Key').split('/')[-1]

    if not filename: 
      # Skip directories
      continue

    try:
      timestamp = datetime.strptime(filename.split('_')[-1], "%Y-%m-%d-%H%M")
    except ValueError:
      timestamp = datetime(2000, 1, 1)  # Older than any data

    s3_file = {
        "filename": filename,
        "url": URL_PREFIX + element.get('Key'),
        "last_modified": element.get("LastModified").strftime('%Y-%m-%dT%H:%M:%SZ'),
        # Change timestamp to date parsed from filename
        "timestamp": timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
      }
    items.append(s3_file)

  return jsonify(items)

'''
Responds with a json containing every other item in the predictions directory
'''
@app.route('/example-predictions', methods=['GET'])
def return_examples_prediction_urls():
  path = EX_PREDICTIONS_DIR + request.args.get('band', 'C07') + '/'
  s3_response = s3_client.list_objects_v2(Bucket=BUCKET, Prefix=path)
  contents = s3_response.get("Contents")
  if not contents:
    return "Path does not exist", 404
  predictions = []  # [oldest...newest]
  timestamp = None

  for element in contents:
    filename = element.get('Key').split('/')[-1]

    if not filename: 
      # Skip directories
      continue

    if not timestamp:
      try:
        timestamp = datetime.strptime(filename.split('_')[-1], "%Y-%m-%d-%H%M")
      except ValueError:
        return "Date and time in filename formatted incorrectly", 400

    timestamp = timestamp + timedelta(minutes=10)

    s3_file = {
        "filename": filename,
        "url": URL_PREFIX + element.get('Key'),
        "last_modified": element.get("LastModified").strftime('%Y-%m-%dT%H:%M:%SZ'),
        # Change timestamp to date parsed from filename
        "timestamp": timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
      }

    for i, p in enumerate(predictions):
      # inserts if timestamp is older than p['timestamp']
      if timestamp < datetime.strptime(p['timestamp'], '%Y-%m-%dT%H:%M:%SZ'):
        predictions.insert(i, s3_file)
        break
    predictions.append(s3_file)


  return jsonify(predictions)

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=5000)
