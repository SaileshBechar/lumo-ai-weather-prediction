 
import tensorflow as tf
import numpy as np
from datetime import datetime, timedelta
import boto3 
from botocore import UNSIGNED
from botocore.config import Config
import matplotlib.patches as mpatches
import io
import os

from tfrecordFormat import get_dataset_grib,graphGrib,grib_png,parsegrib#,plot_animation_grib

#from tfrecordFormat import getS3FileNames#,plot_animation_grib
from mrms_nowcasting import MRMSNowCastingFunctions

#read tf record and call function
w_specBounds = [-82.2, -79.35576, 42.7, 44.603355]

def getS3FileNames(TFRecordPath,basePath,numFiles):
        s3_client = boto3.client( 's3',
            aws_access_key_id="AKIAWRHKEEZVRHAQDW6L",
            aws_secret_access_key="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",
            region_name="us-east-1"
        )
        os.makedirs(basePath, exist_ok =True)    
        response = s3_client.list_objects_v2(Bucket="lumo-app", Prefix=TFRecordPath)#Prefix="test-predictions/grib_24hr/")

        #result = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        filenames = []
        if 'Contents' not in response:
            print('no data')
            return []
        for item in response['Contents']:
            files = item['Key']
            if( ".gz" in files):
                print(files)

                if( len(filenames) >= numFiles):
                    return filenames
                
                filename = files.split('/')[-1]
                print(filename)
                filenames.append(basePath+filename) 
                if(os.path.exists(basePath+filename)  == False):
                    s3_client.download_file("lumo-app",files, basePath+filename)

        return filenames

def FilesToConvert(i,filename,gribGroundTruthsPath):
  print(f'index {i}')
  print(filename)
  dataset = tf.data.TFRecordDataset(filename, compression_type="GZIP") 
   
  print(dataset) 
  dataset = dataset.map(parsegrib) 
  print(dataset)
  grib_row = next(iter(dataset))

  w_specBounds = [-82.2, -79.35576, 42.7, 44.603355]

  #graphGrib(grib_row)
  #grib_row['latitude']  = grib_row['latitude'][768:2304] 
  #grib_row['longitude'] = grib_row['longitude'][4204:5484]- 360 
  #grib_row['radar_frames'] = grib_row['radar_frames'][768:2304, 4204:5484]

  grib_row['longitude'] = grib_row['longitude'][4844:5100]
  grib_row['latitude'] = grib_row['latitude'][1000:1256]
  grib_row['radar_frames'] =  grib_row['radar_frames'][1000:1256, 4844:5100] #rescale_linear(tmp['radar_frames'][i][1000:1256, 4844:5100].numpy(), 0, 20) #tmp['radar_frames'][i][1000:1256, 4844:5100]

  print('zoom in')
  #graphGrib(grib_row,w_specBounds)

  print('create png')
  grib_png(grib_row,i,gribGroundTruthsPath,w_specBounds)

  

fn  = MRMSNowCastingFunctions()

tfRecords = "test-predictions/mrms_24hr/" # where to pull files 
gribGroundTruthsPath = "examples/ground-truths/grib_1hr/"# where to save
gribGroundTruthsPath = "examples/ground-truths/grib_24hr/"
gribGroundTruthsPath = "test-predictions/mrms_grib/"#"examples/ground-truths/mrms_1hr/" #"examples/ground-truths/mrms_24/"
#gribGroundTruthsPath = "mrms_24hr/"

# get files list
#TFRecordPath,basePath,numFiles
def generateGroundTruth_1hr(tfRecords,gribGroundTruthsPath,basePath):
  filenames = getS3FileNames(tfRecords,basePath,13)

  s3_client = boto3.client( 's3',
          aws_access_key_id="AKIAWRHKEEZVRHAQDW6L",
          aws_secret_access_key="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",
          region_name="us-east-1"
    )
      
  response = s3_client.list_objects_v2(Bucket="lumo-app", Prefix=gribGroundTruthsPath)
  if 'Contents' in response:
      for object in response['Contents']:
          print('Deleting', object['Key'])
          s3_client.delete_object(Bucket="lumo-app", Key=object['Key'])


  print(filenames[4:])
  print(len(filenames[4:]))
  if(len(filenames[4:]) < 9 ):
    return False 
  for i,fileName in enumerate(filenames[4:]):
    FilesToConvert(i,fileName,gribGroundTruthsPath)
   
  os.remove(filenames[0])

  return True

'''
basePath = "./data_1hr/"
filenames =  getS3FileNames(tfRecords,basePath,13)
print(filenames)
'''
 
