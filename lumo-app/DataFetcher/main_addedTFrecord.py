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

from tfrecordFormat import save_mrms_as_tfrecord
import xarray as xr
import gc

from grib_precipitation_nowcasting import GribReadAndPredict
from tfrecord_png import generateGroundTruth_1hr #(tfRecords,gribGroundTruthsPath,basePath) FilesToConvert

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
    #print(latest_line)
    dt = re.search("\d{2}-\w{3}-\d{4} \d{2}:\d{2}", latest_line).group(0)
    #print(dt)
    dt_obj = datetime.strptime(dt, "%d-%b-%Y %H:%M")

    return dt_obj

def get_latest_mrms_datetime_24hr():
    url = "https://mrms.ncep.noaa.gov/data/2D/RadarOnly_QPE_24H/"
    response = requests.get(url)

    latest_line = ""
    for line in response.iter_lines():
        if "latest" in str(line):
            latest_line = str(line)
    #print(latest_line)
    dt = re.search("\d{2}-\w{3}-\d{4} \d{2}:\d{2}", latest_line).group(0)
    #print(dt)
    dt_obj = datetime.strptime(dt, "%d-%b-%Y %H:%M")

    return dt_obj

def get_latest_mrms(hrDownload):
    dt_obj = get_latest_mrms_datetime()
    url = "https://mrms.ncep.noaa.gov/data/2D/RadarOnly_QPE_01H/MRMS_RadarOnly_QPE_01H.latest.grib2.gz"
    filename = f"{dt_obj.year}-{dt_obj.month:02}-{dt_obj.day:02}-{dt_obj.hour:02}{dt_obj.minute:02}-radar_1hr"

    if(hrDownload == False ):
        dt_obj = get_latest_mrms_datetime_24hr()
        url = "https://mrms.ncep.noaa.gov/data/2D/RadarOnly_QPE_24H/MRMS_RadarOnly_QPE_24H.latest.grib2.gz"
        filename = f"{dt_obj.year}-{dt_obj.month:02}-{dt_obj.day:02}-{dt_obj.hour:02}{dt_obj.minute:02}-radar_24hr"

    print(f"Downloading {filename}")
    download(url, f"{tmp_path}/{filename}.grib2.gz")

    return f"{filename}"

goes_bands = ["07", "08", "09", "10", "13", "14", "16"]
latest_goes = {}
tmp_path = "tmp"

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

def get_mrms(lumo_client,savePath,hrDownload):

    mrms_dt = get_latest_mrms_datetime() 
    mrms_dt_24 = get_latest_mrms_datetime_24hr()
    if (mrms_dt not in latest_mrms_1hr and hrDownload == True) or (mrms_dt_24 not in latest_mrms_24hr and hrDownload == False) :
        print('grabbing latest')
        filename = get_latest_mrms(hrDownload)
        with gzip.open(f"./{tmp_path}/{filename}.grib2.gz", 'rb') as f_in:
            with open(f"./{tmp_path}/{filename}.grib2", 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        ds = xr.open_dataset(f"./{tmp_path}/{filename}.grib2",  engine="cfgrib" )
        print(ds.unknown)
        #print(ds.unknown.attrs)
        save_mrms_as_tfrecord( f"{tmp_path}/{filename}", ds.unknown)

        # Upload to s3
        print()
        print(f"Uploading {filename}")
        res = s3_upload_file(lumo_client, f"{tmp_path}/{filename}.tfrecord.gz", "lumo-app", f"{savePath}/{filename}.tfrecord.gz")

        #res = s3_upload_file(lumo_client, f"{tmp_path}/{filename}.grib2", "lumo-app", f"mrms/{filename}.grib2")

        # Delete file
        os.remove(f"{tmp_path}/{filename}.tfrecord.gz") # are we deleting the grib
        os.remove(f"{tmp_path}/{filename}.grib2") # are we deleting the grib
        os.remove(f"{tmp_path}/{filename}.grib2.gz")
        os.remove(f"{tmp_path}/{filename}.grib2.923a8.idx") # are we deleting the grib

        if(hrDownload == True):
            print('latest 1hr')
            latest_mrms_1hr.append(mrms_dt)
        else:
            print('latest 24hr')
            latest_mrms_24hr.append(mrms_dt_24)

def clean_mrms(lumo_client,cleanPath):
    mrms_files = lumo_client.list_objects(Bucket="lumo-app", Prefix=cleanPath)
    print('clean mrms')
    if "Contents" not in mrms_files:
        return

    mrms_files = mrms_files["Contents"]
    mrms_files.sort(key=lambda x: x["LastModified"], reverse=True)
    oldest = mrms_files[-1]
    print("Deleting " + oldest['Key'])
    lumo_client.delete_object(Bucket="lumo-app", Key=oldest["Key"])

    old_files = mrms_files[50:]
    for f in old_files:
        print("Deleting " + {f['Key']})
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

def generate_rmse(gt_arr, pred_arr, band):
    rmse = np.empty(gt_arr.shape[0])
    for frame in range(gt_arr.shape[0]):
        rmse[frame] = 0
        for i in range(gt_arr.shape[1]):
            for j in range(gt_arr.shape[2]):
                rmse[frame] += (pred_arr[frame, i, j] - gt_arr[frame, i, j]) * (pred_arr[frame, i, j] - gt_arr[frame, i, j])
        rmse[frame] /= gt_arr.shape[1] * gt_arr.shape[2]
        rmse[frame] = math.sqrt(rmse[frame])

def plot_rmse(rmse_arr, band, num_frames):
    s3_client = boto3.client( 's3',
                aws_access_key_id="AKIAWRHKEEZVRHAQDW6L",
                aws_secret_access_key="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",
                region_name="us-east-1"
            )
            
    response = s3_client.list_objects_v2(Bucket="lumo-app", Prefix="examples/rmse/C" + band + "/")
    if 'Contents' in response:
        for object in response['Contents']:
            print('Deleting', object['Key'])
            s3_client.delete_object(Bucket="lumo-app", Key=object['Key'])
    
    fig = plt.figure(figsize=(10, 10))
    plt.title("Root Mean Squared Error For Band " + band)
    plt.xlabel("Time In Future (mins)")
    plt.ylabel("RMSE")
    plt.scatter(np.arange(1, num_frames + 1)  * 10, rmse_arr, c="#5DA9E9")
    plt.plot(np.arange(1, num_frames + 1) * 10, rmse_arr, c="#766C7F")

    img_data = io.BytesIO()
    fig.savefig(img_data, format='png', bbox_inches='tight')
    img_data.seek(0)
        
    session = boto3.Session(
        aws_access_key_id="AKIAWRHKEEZVRHAQDW6L",
        aws_secret_access_key="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",
    )
    s3 = session.resource('s3')
    bucket = s3.Bucket("lumo-app")
    bucket.put_object(Body=img_data, ContentType='image/png', Key="examples/rmse/C" + band + "/" + "rmse_plot")

    plt.close()

if __name__ == "__main__":
    path = os.path.join("tmp") #"home", "es_bot", "lumo-app", "DataFetcher",
    os.makedirs(path, exist_ok=True)

    for band in goes_bands:
        latest_goes[band] = []

    latest_mrms_1hr = []
    latest_mrms_24hr = []

    #lumo_session = boto3.Session()

    lumo_session = boto3.Session(
          aws_access_key_id="AKIAWRHKEEZVRHAQDW6L",
          aws_secret_access_key="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",
      )
    lumo_client = lumo_session.client("s3")

    goes_session = boto3.Session()
    goes_client = goes_session.client('s3', config=Config(signature_version=botocore.UNSIGNED))
    
    sleep_counter = 0 
    gc.collect()
    while True:
        #break
        print(f'sleep counter : {sleep_counter}')
        print('downloading mrms 1 hr files')
        # get 1 hr files
        get_mrms(lumo_client,"mrms_1hr",True)

        # predict on first 4 : delete oldest file used 
        print('predict 1hr')
        basePath = "./data_1hr/"
        result = GribReadAndPredict("mrms_1hr/","mrms-predictions/mrms_1h/",basePath,13)
        # ground truth clean old and generate
        # store 9 latest as ground truth : inside mrms function 
        #FilesToConvert(i,filename,gribGroundTruthsPath)
        result = generateGroundTruth_1hr("mrms_1hr/","mrms-ground-truths/",basePath)
        # clean 1 hr makes sure atleast 4 files left
        if( result == True ):
            clean_mrms(lumo_client,"mrms_1hr/")  # check only triggers when more than 50
        # if statemetn w counter for 24hr : then same process
        # download 24hrs
        
        if(sleep_counter == 0):
            print('downloading mrms 24 hr files')
            basePath = "./data_24hr/"
            get_mrms(lumo_client,"mrms_24hr",False) 
            #print('predict 24hr')
            result = GribReadAndPredict("mrms_24hr/","mrms-predictions/mrms_24h/",basePath,4)

            if( result == True ):
                clean_mrms(lumo_client,"mrms_24hr/") 

            sleep_counter += 1
            # predict and delete oldest
        if(sleep_counter > 5): #5
            sleep_counter = 0 
        else:
            sleep_counter += 1
            time.sleep(60 * 2)
        # clean mrms 24 
        
        #clean_goes(lumo_client)
        print('sleep')
        gc.collect()
        time.sleep(60 * 6)
        #break
