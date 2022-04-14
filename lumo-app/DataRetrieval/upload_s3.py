import os
from dotenv import load_dotenv
import pickle
import boto3
from botocore.exceptions import NoCredentialsError

# .env file required to run this script
# should contain:
# - AWS_ACCESS_KEY_ID="<AWS ACCESS KEY>"
# - AWS_SECRET_ACCESS_KEY="<AWS SECRET KEY>"

load_dotenv()

ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# inputs:
# - local_file: local file location that will be uploaded to S3
# - bucket: place in S3 where the local file will be uploaded to 
# - s3_file: name of the file that will be uploaded to S3
def upload_to_aws(local_file, bucket, s3_file):
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)

    try:
        s3.upload_file(local_file, bucket, s3_file)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False

# test function that creates an arbitrary pickle file
def create_pickle():
    test = {'key' : '2110', 'filename' : '2110', 'filetype' : 'png'}

    db = {}
    db['2110'] = test

    dbfile = open('test/2110', 'ab')

    pickle.dump(db, dbfile)
    dbfile.close()

create_pickle()

uploaded_png = upload_to_aws('test/2110.png', 'lumo-test-bucket', 'test.png')
uploaded_pickle = upload_to_aws('test/2110', 'lumo-test-bucket', 'test')

