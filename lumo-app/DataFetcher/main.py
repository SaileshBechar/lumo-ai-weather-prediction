import boto3
import botocore
import gzip
import os
import re
import requests
import shutil
import time

import pprint

from botocore.config import Config
from botocore.exceptions import ClientError
from datetime import timezone
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# This was taken from https://stackoverflow.com/a/62743933
def download(url: str, file_path='', attempts=2):
    """Downloads a URL content into a file (with large file support by streaming)

    :param url: URL to download
    :param file_path: Local file name to contain the data downloaded
    :param attempts: Number of attempts
    :return: New file path. Empty string if the download failed
    """
    if not file_path:
        file_path = os.path.realpath(os.path.basename(url))
    url_sections = urlparse(url)
    if not url_sections.scheme:
        url = f'http://{url}'
    for attempt in range(attempts):
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                with open(file_path, 'wb') as out_file:
                    for chunk in response.iter_content(chunk_size=1024*1024): # 1MB chunks
                        out_file.write(chunk)
                return file_path
        except Exception as ex:
            print(f'Attempt #{attempt} failed with error: {ex}')
    return ''

# This was taken from https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html
def s3_upload_file(s3_client, file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        print(f"Upload filed with error: {e}")
        return False
    return True

def get_latest_mrms_datetime():
    url = "https://mrms.ncep.noaa.gov/data/2D/RadarOnly_QPE_01H/"
    response = requests.get(url)

    latest_line = ""
    for line in response.iter_lines():
        if "latest" in str(line):
            latest_line = str(line)

    dt = re.search("\d{2}-\w{3}-\d{4} \d{2}:\d{2}", latest_line).group(0)

    dt_obj = datetime.strptime(dt, "%d-%b-%Y %H:%M")

    return dt_obj

def get_latest_mrms():
    dt_obj = get_latest_mrms_datetime()

    url = "https://mrms.ncep.noaa.gov/data/2D/RadarOnly_QPE_01H/MRMS_RadarOnly_QPE_01H.latest.grib2.gz"

    filename = f"{dt_obj.year}-{dt_obj.month:02}-{dt_obj.day:02}-{dt_obj.hour:02}{dt_obj.minute:02}-radar"

    print(f"Downloading {filename}")
    download(url, f"{tmp_path}/{filename}.grib2.gz")

    return f"{filename}"

goes_bands = ["07", "08", "09", "10", "13", "14"]
latest_goes = {}
tmp_path = "/home/es_bot/lumo-app/DataFetcher/tmp"

def get_latest_goes(lumo_client, goes_client):
    utc_now = datetime.now(timezone.utc)

    data = goes_client.list_objects_v2(Bucket="noaa-goes16", Prefix=f"ABI-L2-CMIPF/{utc_now.year}/{utc_now.strftime('%j')}/{utc_now.strftime('%H')}")

    if "Contents" not in data:
        return

    contents = data["Contents"]
    contents.sort(key=lambda x: x["LastModified"], reverse=True)

    for band in goes_bands:
        entry = next(x for x in contents if f"M6C{band}" in x["Key"])

        file_time = entry["Key"].split("_")[-1][1:-4]

        dt_obj = datetime.strptime(file_time, "%Y%j%H%M%S")

        filename = f"{dt_obj.year}-{dt_obj.month:02}-{dt_obj.day:02}-{dt_obj.hour:02}{dt_obj.minute:02}-goes-C{band}"

        if filename not in latest_goes[band]:
            print(f"Downloading {filename}")
            goes_client.download_file("noaa-goes16", entry["Key"], f"{tmp_path}/{filename}.nc")

            print(f"Uploading to goes/C{band}/{filename}.nc")
            s3_upload_file(lumo_client, f"{tmp_path}/{filename}.nc", "lumo-app", f"goes/C{band}/{filename}.nc")

            os.remove(f"{tmp_path}/{filename}.nc")

            latest_goes[band].append(filename)

def clean_mrms(lumo_client):
    mrms_files = lumo_client.list_objects(Bucket="lumo-app", Prefix="mrms/")

    if "Contents" not in mrms_files:
        return

    mrms_files = mrms_files["Contents"]
    mrms_files.sort(key=lambda x: x["LastModified"], reverse=True)
    old_files = mrms_files[50:]
    for f in old_files:
        print(f"Deleting {f['Key']}")
        lumo_client.delete_object(Bucket="lumo-app", Key=f["Key"])

def clean_goes(lumo_client):
    for band in goes_bands:
        goes_files = lumo_client.list_objects(Bucket="lumo-app", Prefix=f"goes/C{band}/")

        if "Contents" not in goes_files:
            return

        goes_files = goes_files["Contents"]
        goes_files.sort(key=lambda x: x["LastModified"], reverse=True)
        old_files = goes_files[50:]
        for f in old_files:
            print(f"Deleting {f['Key']}")
            lumo_client.delete_object(Bucket="lumo-app", Key=f["Key"])

    return

if __name__ == "__main__":
    path = os.path.join("home", "es_bot", "lumo-app", "DataFetcher", "tmp")
    os.makedirs(path, exist_ok=True)

    for band in goes_bands:
        latest_goes[band] = []

    latest_mrms = []

    lumo_session = boto3.Session()
    lumo_client = lumo_session.client("s3")

    goes_session = boto3.Session()
    goes_client = goes_session.client('s3', config=Config(signature_version=botocore.UNSIGNED))

    while True:
        mrms_dt = get_latest_mrms_datetime()
        if mrms_dt not in latest_mrms:
            filename = get_latest_mrms()
            with gzip.open(f"{tmp_path}/{filename}.grib2.gz", 'rb') as f_in:
                with open(f"{tmp_path}/{filename}.grib2", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Upload to s3
            print(f"Uploading {filename}")
            res = s3_upload_file(lumo_client, f"{tmp_path}/{filename}.grib2", "lumo-app", f"mrms/{filename}.grib2")

            # Delete file
            os.remove(f"{tmp_path}/{filename}.grib2")
            os.remove(f"{tmp_path}/{filename}.grib2.gz")

            latest_mrms.append(mrms_dt)

        get_latest_goes(lumo_client, goes_client)

        clean_mrms(lumo_client)
        clean_goes(lumo_client)

        time.sleep(60 * 2)
