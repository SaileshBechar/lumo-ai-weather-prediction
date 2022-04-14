import GOES
import numpy as np
import re
import os
from pathlib import Path
from goes_py.GoesData import GoesData
import tensorflow as tf

class Plot:

    def __init__(self, path):
        self.download_path = path
        self.full_disk_boundary = [-156.2995, 6.2995, -81.3282, 81.3282]
        self.conus_boundary = [-135, -66, 25, 50]
        self.image_dict = {}

    def download_images(self, product, date, time_start, time_end, band):
        path = self.download_path + date + "/C" + band + '/'
        Path(path).mkdir(parents=True, exist_ok=True)

        GOES.download('goes16', 'ABI-L2-' + product,
                            DateTimeIni = date + '-' + time_start, DateTimeFin = date + '-' + time_end,
                            # channel=['07-10', '13-14', '16'], rename_fmt = '%Y%m%d%H%M', path_out=path)
                            channel=[band], rename_fmt = '%Y%m%d%H%M', path_out=path) # download 1 band for now
    
    def decode_netCDF(self, date, band, crop_size=256):
        path = self.download_path + date + "/" + "C" + band + "/"
        if Path(path).is_dir() == False:
            self.image_dict = {}
            return
        directory = os.listdir(path)
        dir_str = (' ').join(directory)        
        cmip_pattern = re.compile(r'OR_ABI-L2-CMIPF-M6C\w*\.nc') # old convention of datetime
        # cmip_pattern = re.compile(r'\d{4}-\d{2}-\d{2}-\d{4}-goes-C' + re.escape(band) + r'.nc')

        for file_name in re.findall(cmip_pattern, dir_str):
            print(file_name)
            goesData = GoesData(Path(path + file_name),
                                'CMI', self.full_disk_boundary, 1)
            list_of_crops = goesData.generate_latlong_crop(crop_size,lat=40,long=-84) # Lower left corner
            self.concat_imgs_of_same_latlong(list_of_crops)

    def concat_imgs_of_same_latlong(self, list_of_crops):
        for image in list_of_crops:
            latlong = image.get_latlong()
            date_time = image.date + "_" + str(image.timestamp)[:-4] # strips timestamp of last 4 digits
            if self.image_dict.get(latlong) == None: # maintain list of images organized by their position on map
                image.img = image.img[:,:,np.newaxis]
                self.image_dict[latlong] = {date_time : image}
            else:
                if self.image_dict[latlong].get(date_time) == None: # maintain sublist of images organized by their timestamp
                    image.img = image.img[:,:,np.newaxis]
                    self.image_dict[latlong][date_time] = image
                else:
                    goes_image = self.image_dict[latlong][date_time]
                    goes_image.concat_imgs_with_shared_timestamp(image) # if two images share latlong and timestamp, add them together
                                                                        # becuase the only difference is their bands
    def save_all_coverted_crops(self, num_frames):
        timeseries_of_crops = []
        for lat_long_dict in self.image_dict.values():
            for date_timestamp in lat_long_dict:
                timeseries_of_crops.append(lat_long_dict[date_timestamp])
                if len(timeseries_of_crops) == num_frames:
                    path = self.download_path + "/output/" + date_timestamp[:10] + "/" + "C" + str(timeseries_of_crops[num_frames -1].band) + "/" 
                    Path(path).mkdir(parents=True, exist_ok=True)
                    self.save_as_tfrecord(path + str(timeseries_of_crops[num_frames -1].timestamp)[:10] , timeseries_of_crops)
                    timeseries_of_crops = []
                    self.image_dict = {}
                    
    def save_as_tfrecord(self, path, arr):
        # Convert arr (list of GoesImages) to tfrecord format
        # Concat all timesteps into one np array
        img_size_x = arr[0].img.shape[0]
        img_size_y = arr[0].img.shape[1]
        radar_frames = np.empty((0,img_size_x,img_size_y,1))
        for goes_image in arr:
            radar_frames = np.append(radar_frames, np.expand_dims(goes_image.img, axis=0), axis=0)

        tfoptions = tf.io.TFRecordOptions(compression_type="GZIP")
        with tf.io.TFRecordWriter(path + ".tfrecord.gz", options=tfoptions) as writer:
            tfrecord = self.create_tfrecord(radar_frames, arr)
            serialized_tfrecord = tfrecord.SerializeToString()
            writer.write(serialized_tfrecord)

    def bytes_feature(self, value):
        """Returns a bytes_list from a string / byte."""
        if isinstance(value, type(tf.constant(0))): # if value ist tensor
            value = value.numpy() # get value of tensor
        return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))

    def float_feature(self, value):
        """Returns a float_list from a float / double."""
        return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))

    def int64_feature(self, value):
        """Returns an int64_list from a bool / enum / int / uint."""
        return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))

    def serialize_array(self, array):
        array = tf.io.serialize_tensor(array)
        return array

    def create_tfrecord(self, example, metadata):
        feature = {
            "radar": self.bytes_feature(self.serialize_array(example)), # tf.string
            "lonmin": self.float_feature(metadata[0].latlong_box[0]), # tf.float32
            "lonmax": self.float_feature(metadata[0].latlong_box[1]), # tf.float32
            "latmin": self.float_feature(metadata[0].latlong_box[2]), # tf.float32
            "latmax": self.float_feature(metadata[0].latlong_box[3]), # tf.float32
            "lonmin_xy": self.float_feature(metadata[0].xy_box[0]), # tf.float32
            "lonmax_xy": self.float_feature(metadata[0].xy_box[1]), # tf.float32
            "latmin_xy": self.float_feature(metadata[0].xy_box[2]), # tf.float32
            "latmax_xy": self.float_feature(metadata[0].xy_box[3]), # tf.float32
            "end_time_timestamp": self.int64_feature(int(metadata[len(metadata) - 1].timestamp)), # tf.int64
            "band" : self.bytes_feature(metadata[0].band.encode('utf-8')),
            "num_frames" : self.int64_feature(example.shape[0]),
            "height" : self.int64_feature(example.shape[1]),
            "width" : self.int64_feature(example.shape[2])
        }
        return tf.train.Example(features=tf.train.Features(feature=feature))