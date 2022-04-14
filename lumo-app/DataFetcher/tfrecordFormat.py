 
import tensorflow as tf
import numpy as np
from datetime import datetime, timedelta

import boto3 
from botocore import UNSIGNED
from botocore.config import Config
import matplotlib.patches as mpatches
import io
import os

import datetime
import os
import cartopy

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import animation
import numpy as np
import matplotlib.colors as mcolors
from pyproj import Proj

_MM_PER_HOUR_INCREMENT = 1/32.
_MAX_MM_PER_HOUR = 128.
_INT16_MASK_VALUE = -1

def test():
    print('does this work')
    
# code to save tf records
def serialize_array( array):
    array = tf.io.serialize_tensor(array)
    return array

def bytes_feature( value):
        """Returns a bytes_list from a string / byte."""
        if isinstance(value, type(tf.constant(0))): # if value ist tensor
            value = value.numpy() # get value of tensor
        return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

def int64_feature( value):
        """Returns an int64_list from a bool / enum / int / uint."""
        return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

def float_feature( value):
        """Returns a float_list from a float / double."""
        return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))

def create_tfrecord( example, metadata,arr):
    #ds.unknown
    #lons =
    ns = 1e-9
    
    feature = {
        "radar": bytes_feature(serialize_array(example)), # tf.string
        "sample_prob": float_feature(1.),  # tf.float32
        "latitude":bytes_feature(serialize_array(arr.latitude)),
        "longitude": bytes_feature(serialize_array(arr.longitude)),
        "lonmin": int64_feature(int(metadata['GRIB_longitudeOfFirstGridPointInDegrees'])),#(metadata[0].latlong_box[0]), # tf.int64
        "lonmax": int64_feature(int(metadata['GRIB_longitudeOfLastGridPointInDegrees'])),#(metadata[0].latlong_box[1]), # tf.int64
        "latmin": int64_feature(int(metadata['GRIB_latitudeOfFirstGridPointInDegrees'])),#(metadata[0].latlong_box[2]), # tf.int64
        "latmax": int64_feature(int(metadata['GRIB_latitudeOfLastGridPointInDegrees'])),#(metadata[0].latlong_box[3]), # tf.int64
        "end_time_timestamp": int64_feature(int(arr.time.data.astype(int) * ns)) # tf.int64
    }
    return tf.train.Example(features=tf.train.Features(feature=feature))

def save_mrms_as_tfrecord( path, arr):
    # Convert arr (list of GoesImages) to tfrecord format
    # Concat all timesteps into one np array
    #radar_frames = np.empty((0,256,256,arr[0].num_bands))
    #for goes_image in arr:
    #    radar_frames = np.append(radar_frames, np.expand_dims(goes_image.img, axis=0), axis=0)
    #radar_frames = masked_array(prcpvar[:], units(prcpvar.units.lower())).to('mm')

    #tfoptions = tf.io.TFRecordOptions(2) # 2 = GZIP
    tfoptions = tf.io.TFRecordOptions(compression_type="GZIP")
    with tf.io.TFRecordWriter(path + ".tfrecord.gz", options=tfoptions) as writer:
        tfrecord = create_tfrecord(arr.data, arr.attrs,arr)
        serialized_tfrecord = tfrecord.SerializeToString()
        writer.write(serialized_tfrecord)


#code to read tf records
def rescale_linear(array, new_min, new_max):
    """Rescale an arrary linearly."""
    minimum, maximum = np.min(array), np.max(array)
    m = (new_max - new_min) / (maximum - minimum)
    b = new_min - m * minimum
    return m * array + b

def parsegrib(element):
    print('parsing')
    
    features = {
      'latmin': tf.io.FixedLenFeature([], tf.int64), 
      'latmax':tf.io.FixedLenFeature([], tf.int64),
      'radar' : tf.io.FixedLenFeature([], tf.string),
      'latitude' : tf.io.FixedLenFeature([], tf.string),
      'longitude' : tf.io.FixedLenFeature([], tf.string),
        
      'lonmin':tf.io.FixedLenFeature([], tf.int64),
      'lonmax':tf.io.FixedLenFeature([], tf.int64),
      'end_time_timestamp':tf.io.FixedLenFeature([], tf.int64)  
        
    }
    
    
    result = tf.io.parse_single_example(element, features) 
    radar_bytes = result['radar']#result.pop("radar")
    shape = (3500, 7000)

    radar_float32 = tf.reshape(tf.io.parse_tensor(radar_bytes, tf.float32), shape)
    #print('radar bytes')
    #print(radar_bytes)
    result['latitude'] = tf.io.parse_tensor(result['latitude'], tf.float64) 
    result['longitude'] = tf.io.parse_tensor(result['longitude'], tf.float64)

    result['latitude'] = tf.cast(result['latitude'], tf.float32) 
    result['longitude'] = tf.cast(result['longitude'], tf.float32)


    mask = tf.not_equal(radar_float32, _INT16_MASK_VALUE)

    #radar = radar_float64 * _MM_PER_HOUR_INCREMENT
    radar = tf.clip_by_value(
      radar_float32, _INT16_MASK_VALUE * _MM_PER_HOUR_INCREMENT, _MAX_MM_PER_HOUR)

    return {'radar_frames':radar,
            "radar_mask":mask,
            'latmin':result['latmin'],
            'latmax':result['latmax'],
            'lonmin':result['lonmin'], 
            'lonmax': result['lonmax'],
            'longitude':result['longitude'],
            'latitude':result['latitude'],
            'end_time_timestamp':result['end_time_timestamp']}

def get_dataset_grib(filename):
  #create the dataset
  #dataset = tf.data.TFRecordDataset(filename)

  #pass every single feature through our mapping function
  #dataset = dataset.map(
  #    parse_tfr_element
  #)
    dataset = tf.data.TFRecordDataset(filename, compression_type="GZIP") 
   
    print(dataset) 
    dataset = dataset.map(parsegrib)

    return dataset
    
def graphGrib(row,map_extent = [-106.0, -78.05576, 30.0, 47.603355]):
    globe = cartopy.crs.Globe(semimajor_axis=6371200.0) 
    proj = cartopy.crs.Stereographic(central_latitude=90, 
                    central_longitude= -105,
                    true_scale_latitude=60, 
                    globe=globe)
 
    fig = plt.figure(figsize=(10, 10))
    crs = cartopy.crs.PlateCarree()
    ax = plt.axes(projection=crs)
    
    ax.set_extent(map_extent, crs=crs)
    
    # draw coastlines, state and country boundaries, edge of map.
    ax.coastlines()
    ax.add_feature(cartopy.feature.BORDERS)
    lakes = cartopy.feature.NaturalEarthFeature('physical', 'lakes', '10m')
    ax.add_feature(lakes, edgecolor='black', linewidth=0.25)

    waterloo = mpatches.Circle((-80.516670, 43.466667), 0.065, linestyle='solid', edgecolor='black', facecolor='gold')
    ax.add_patch(waterloo)
    big_loo = mpatches.Circle((-80.516670, 43.466667), 0.094, linestyle='solid', edgecolor='gold', facecolor='none')
    ax.add_patch(big_loo)

    data = row['radar_frames']#[500:950, 800:1100] 
    lons = np.array(row['longitude'])
    lats = np.array(row['latitude'])
    
    convert = Proj(proj.proj4_init)
    X, Y = np.meshgrid(lons, lats)
    X, Y = convert(X, Y)
    print(X.shape, Y.shape)
    print(X.min(), X.max(), Y.min(), Y.max())

    cs = ax.imshow(data, extent=[X.min(), X.max(), Y.min(), Y.max()], cmap='jet', vmin=0, vmax=15, origin='upper', interpolation='none', transform=proj)
    # add colorbar.
    cbar = plt.colorbar(cs, orientation='horizontal')
    cbar.set_label("millimeter")

    plt.show()

#code for ground truth
def plot_animation_grib(field,FrameData,map_extent = [-106.0, -78.05576, 30.0, 47.603355],figsize=None,
                   vmin=0, vmax=10, cmap="jet", **imshow_args):
  

    s3_client = boto3.client( 's3',
          aws_access_key_id="",
          aws_secret_access_key="",
          region_name="us-east-1"
    )
      
    response = s3_client.list_objects_v2(Bucket="lumo-app", Prefix="test-predictions/mrms_grib/")
    if 'Contents' in response:
        for object in response['Contents']:
            print('Deleting', object['Key'])
            s3_client.delete_object(Bucket="lumo-app", Key=object['Key'])
  
    for i in range(field.shape[0]):
      print(f'img : {i}')
      globe = cartopy.crs.Globe(semimajor_axis=6371200.0) 
      proj = cartopy.crs.Stereographic(central_latitude=90, 
                      central_longitude= -105,
                      true_scale_latitude=60, 
                      globe=globe)
  
      fig = plt.figure(figsize=(10, 10))
      crs = cartopy.crs.PlateCarree()
      ax = plt.axes(projection=crs)
      
      ax.set_extent(map_extent, crs=crs)
      
      # draw coastlines, state and country boundaries, edge of map.
      ax.coastlines()
      ax.add_feature(cartopy.feature.BORDERS)
      lakes = cartopy.feature.NaturalEarthFeature('physical', 'lakes', '10m')
      ax.add_feature(lakes, edgecolor='gold', linewidth=0.25)

      waterloo = mpatches.Circle((-80.516670, 43.466667), 0.065, linestyle='solid', edgecolor='black', facecolor='gold')
      ax.add_patch(waterloo)
      big_loo = mpatches.Circle((-80.516670, 43.466667), 0.094, linestyle='solid', edgecolor='gold', facecolor='none')
      ax.add_patch(big_loo)

      #data = row['radar_frames']#[500:950, 800:1100] 
      #lons = np.array(row['longitude'])
      #lats = np.array(row['latitude'])
      
      #convert = Proj(proj.proj4_init)
      #X, Y = np.meshgrid(lons, lats)
      #X, Y = convert(X, Y)
      #print(X.shape, Y.shape)
      #print(X.min(), X.max(), Y.min(), Y.max())
      currentlat_lon =  FrameData[1] #img_lat_lon
      bg_frame = np.zeros((3500, 7000))
      print('f')
      print(field[i, ..., 0].shape)
      cs = ax.imshow(field[i, ..., 0], extent=[currentlat_lon[0], currentlat_lon[1], currentlat_lon[2], currentlat_lon[3]], cmap='jet', vmin=vmin, vmax=vmax, origin='upper', interpolation='none', transform=proj)
      # add colorbar.
      cbar = plt.colorbar(cs, orientation='horizontal')
      cbar.set_label("millimeter")

      plt.show()

      img_data = io.BytesIO()
      fig.savefig(img_data, format='png', bbox_inches='tight')
      img_data.seek(0)

      session = boto3.Session(
          aws_access_key_id="",
          aws_secret_access_key="",
      )
      s3 = session.resource('s3')
      bucket = s3.Bucket("lumo-app")

      datetime_str = datetime.datetime.utcfromtimestamp(FrameData[0]).strftime("%Y-%m-%d-%H%M")
      #print(datetime_str)
      index_str = f'0{str(i)}' if i < 10 else str(i)
      bucket.put_object(Body=img_data, ContentType='image/png', Key="test-predictions/mrms_grib/" +  datetime_str+"_"+index_str)

def grib_png(row,index,gribGroundTruthsPath,map_extent = [-106.0, -78.05576, 30.0, 47.603355],figsize=None,
                   vmin=0, vmax=15, cmap="jet", **imshow_args):
  
    #s3Pre = 
    s3_client = boto3.client( 's3',
          aws_access_key_id="",
          aws_secret_access_key="",
          region_name="us-east-1"
    )
      
    response = s3_client.list_objects_v2(Bucket="lumo-app", Prefix="examples/ground-truths/mrms_24/")
    #if 'Contents' in response:
    #    for object in response['Contents']:
    #        print('Deleting', object['Key'])
    #        s3_client.delete_object(Bucket="lumo-app", Key=object['Key'])
  
    #for i in range(field.shape[0]):
    #print(f'img : {i}')
    globe = cartopy.crs.Globe(semimajor_axis=6371200.0) 
    proj = cartopy.crs.Stereographic(central_latitude=90, 
                    central_longitude= -105,
                    true_scale_latitude=60, 
                    globe=globe)

    fig = plt.figure(figsize=(10, 10))
    crs = cartopy.crs.PlateCarree()
    ax = plt.axes(projection=crs)
      
    ax.set_extent(map_extent, crs=crs)
    
    # draw coastlines, state and country boundaries, edge of map.
    ax.coastlines()
    ax.add_feature(cartopy.feature.BORDERS)
    lakes = cartopy.feature.NaturalEarthFeature('physical', 'lakes', '10m')
    ax.add_feature(lakes, edgecolor='gold', linewidth=0.25)

    waterloo = mpatches.Circle((-80.516670, 43.466667), 0.065, linestyle='solid', edgecolor='black', facecolor='gold')
    ax.add_patch(waterloo)
    big_loo = mpatches.Circle((-80.516670, 43.466667), 0.094, linestyle='solid', edgecolor='gold', facecolor='none')
    ax.add_patch(big_loo)

    data = row['radar_frames']#[500:950, 800:1100] 
    lons = np.array(row['longitude'])
    lats = np.array(row['latitude'])
    
    convert = Proj(proj.proj4_init)
    X, Y = np.meshgrid(lons, lats)
    X, Y = convert(X, Y)
    #print(X.shape, Y.shape)
    #print(X.min(), X.max(), Y.min(), Y.max())  
    
    cs = ax.imshow(data, extent=[X.min(), X.max(), Y.min(), Y.max()], cmap='jet', vmin=vmin, vmax=vmax, origin='upper', interpolation='none', transform=proj)
    # add colorbar.
    #cbar = plt.colorbar(cs, orientation='horizontal')
    #cbar.set_label("millimeter")
    #plt.show()

    img_data = io.BytesIO()
    #fig.savefig(img_data, format='png', bbox_inches='tight')
    fig.savefig(img_data, format='png', bbox_inches='tight', facecolor='gold')
    img_data.seek(0)

    session = boto3.Session(
        aws_access_key_id="",
        aws_secret_access_key="",
    )
    s3 = session.resource('s3')
    bucket = s3.Bucket("lumo-app")

    datetime_str = datetime.datetime.utcfromtimestamp(row['end_time_timestamp']).strftime("%Y-%m-%d-%H%M")
    #print(datetime_str)
    #index_str = f'0{str(i)}' if i < 10 else str(i)
    print('creating img')
    index = "{:02d}".format(index)
    bucket.put_object(Body=img_data, ContentType='image/png', Key= gribGroundTruthsPath+index+"_"+datetime_str )


# precipitation nowcasting 