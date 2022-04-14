import datetime
import os
import cartopy

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import animation
import numpy as np
#import shapely.geometry as sgeom
import tensorflow as tf
#import tensorflow_hub
#from google.colab import auth

import matplotlib.colors as mcolors
from pyproj import Proj

import boto3 
from botocore import UNSIGNED
from botocore.config import Config
import matplotlib.patches as mpatches
import io
import os

_MM_PER_HOUR_INCREMENT = 1/32.
_MAX_MM_PER_HOUR = 128.
_INT16_MASK_VALUE = -1
# Fixed values supported by the snapshotted model.
NUM_INPUT_FRAMES = 4
NUM_TARGET_FRAMES = 18

waterloo_specBounds = [-82.2, -79.35576, 42.7, 44.603355]
map_extent_crop = [-86.0, -78.05576, 39.0, 47.603355] 
w_specextent = [-83.2, -78.35576, 41.5, 45.603355]

TFHUB_BASE_PATH = "gs://dm-nowcasting-example-data/tfhub_snapshots"


class MRMSNowCastingFunctions():

    def test(self):
        print('test')

    def rescale_linear(self,array, new_min, new_max):
        """Rescale an arrary linearly."""
        minimum, maximum = np.min(array), np.max(array)
        m = (new_max - new_min) / (maximum - minimum)
        b = new_min - m * minimum
        return m * array + b

    def parsegrib(self,element):
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
        print('radar bytes')
        print(radar_bytes)
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

    def get_dataset_grib(self,filename):
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

    def graphMrms(self,row):
        globe = cartopy.crs.Globe(semimajor_axis=row['earth_radius'].numpy()) 
        proj = cartopy.crs.Stereographic(central_latitude=row['central_latitude'].numpy(), 
                            central_longitude= row['central_longitude'].numpy() ,
                            true_scale_latitude=row['true_scale_latitude'].numpy(), 
                            globe=globe)
    
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(1, 1, 1, projection=proj)

        # draw coastlines, state and country boundaries, edge of map.
        ax.coastlines()
        ax.add_feature(cartopy.feature.BORDERS)
        ax.add_feature(cartopy.feature.STATES)

        # draw filled contours.
        clevs = [0, 1, 2.5, 5, 7.5, 10, 15, 20, 30, 40,
                50, 70, 100, 150, 200, 250, 300, 400, 500, 600, 750]
        # In future MetPy
        # norm, cmap = ctables.registry.get_with_boundaries('precipitation', clevs)
        cmap_data = [(1.0, 1.0, 1.0),
                    (0.3137255012989044, 0.8156862854957581, 0.8156862854957581),
                    (0.0, 1.0, 1.0),
                    (0.0, 0.8784313797950745, 0.501960813999176),
                    (0.0, 0.7529411911964417, 0.0),
                    (0.501960813999176, 0.8784313797950745, 0.0),
                    (1.0, 1.0, 0.0),
                    (1.0, 0.6274510025978088, 0.0),
                    (1.0, 0.0, 0.0),
                    (1.0, 0.125490203499794, 0.501960813999176),
                    (0.9411764740943909, 0.250980406999588, 1.0),
                    (0.501960813999176, 0.125490203499794, 1.0),
                    (0.250980406999588, 0.250980406999588, 1.0),
                    (0.125490203499794, 0.125490203499794, 0.501960813999176),
                    (0.125490203499794, 0.125490203499794, 0.125490203499794),
                    (0.501960813999176, 0.501960813999176, 0.501960813999176),
                    (0.8784313797950745, 0.8784313797950745, 0.8784313797950745),
                    (0.9333333373069763, 0.8313725590705872, 0.7372549176216125),
                    (0.8549019694328308, 0.6509804129600525, 0.47058823704719543),
                    (0.6274510025978088, 0.42352941632270813, 0.23529411852359772),
                    (0.4000000059604645, 0.20000000298023224, 0.0)]
        cmap = mcolors.ListedColormap(cmap_data, 'precipitation')
        norm = mcolors.BoundaryNorm(clevs, cmap.N)

        data = row['radar_frames']#[500:950, 800:1100] 
        x = row['x']#nc.variables['x'][:]
        y = row['y']#nc.variables['y'][:]
        x = np.array(x)
        y = np.array(y)
        cs = ax.contourf(x, y, data, clevs, cmap='jet',vmin= 0,vmax = 15)#cmap=cmap, norm=norm)
        cs = ax.imshow(data, extent=[x.min(), x.max(), y.min(), y.max()], cmap='jet', vmin=0, vmax=15, origin='upper', interpolation='none', transform=proj)
        # add colorbar.
        cbar = plt.colorbar(cs, orientation='horizontal')
        cbar.set_label("millimeter")

        
        # cropp data 
        
        #ax.set_title(prcpvar.long_name + ' for period ending ' + nc.creation_time)
        plt.show()

    def graphGrib(self,row,map_extent = [-106.0, -78.05576, 30.0, 47.603355]):
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

        waterloo = mpatches.Circle((-80.516670, 43.466667), 0.085, linestyle='solid', edgecolor='black', facecolor='gold')
        ax.add_patch(waterloo)
        big_loo = mpatches.Circle((-80.516670, 43.466667), 0.14, linestyle='solid', edgecolor='gold', facecolor='none')
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

    #pull tf records in
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

    def get_dataset(self,filenames):
        #optional if you have more filefolders to got through.
        #return filenames
        print(filenames)
        #print(len(filenames))
        autotune = tf.data.experimental.AUTOTUNE
        
        options = tf.data.Options()
        options.experimental_deterministic = False
        #records = tf.data.Dataset.list_files(folder_path + '/*',shuffle=True).with_options(options)

        ds = tf.data.TFRecordDataset(filenames, compression_type="GZIP",
                            num_parallel_reads=autotune).repeat()
        ds = ds.map(self.parsegrib, num_parallel_calls=autotune)
        ds = ds.batch(len(filenames))
        ds = ds.prefetch(autotune)
        return ds

    def plotBounds(self,lons,lats):
        globe = cartopy.crs.Globe(semimajor_axis=6371200.0) 
        proj = cartopy.crs.Stereographic(central_latitude=90, 
                            central_longitude= -105,
                            true_scale_latitude=60, 
                            globe=globe)
        
        lons = np.array(lons)#row['longitude'])
        lats = np.array(lats)#row['latitude'])
        
        convert = Proj(proj.proj4_init)
        X, Y = np.meshgrid(lons, lats)
        X, Y = convert(X, Y)
        #print(X.shape, Y.shape)
        print(X.min(), X.max(), Y.min(), Y.max())
        return [X.min(), X.max(), Y.min(), Y.max()]

    def plot_animation_grib(self,field,gribGroundTruthsPath,FrameData,map_extent = [-106.0, -78.05576, 30.0, 47.603355],figsize=None,
                    vmin=0, vmax=10, cmap="jet", **imshow_args):
    

        s3_client = boto3.client( 's3',
            aws_access_key_id="AKIAWRHKEEZVRHAQDW6L",
            aws_secret_access_key="JF3BJEi1FcBwEBaisIK5FAIOV9NzF83yEMEzQQoh",
            region_name="us-east-1"
        )
        #s3://lumo-app/examples/predictions/mrms_24hr/  
        response = s3_client.list_objects_v2(Bucket="lumo-app", Prefix="test-predictions/mrms_24hr/") #Prefix="test-predictions/mrms_grib/")
        #if 'Contents' in response:
        #    for object in response['Contents']:
        #        print('Deleting', object['Key'])
        #        s3_client.delete_object(Bucket="lumo-app", Key=object['Key'])
    
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
            #cbar = plt.colorbar(cs, orientation='horizontal')
            #cbar.set_label("millimeter")

            plt.show()

        img_data = io.BytesIO()
        #fig.savefig(img_data, format='png', bbox_inches='tight')
        fig.savefig(img_data, format='png', bbox_inches='tight', facecolor='gold')
        img_data.seek(0)

        session = boto3.Session(
            aws_access_key_id="AKIAWRHKEEZVRHAQDW6L",
            aws_secret_access_key="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",
        )
        s3 = session.resource('s3')
        bucket = s3.Bucket("lumo-app")

        datetime_str = datetime.datetime.utcfromtimestamp(FrameData[0][3]).strftime("%Y-%m-%d-%H%M")
        print(datetime_str)
        index_str = f'0{str(i)}' if i < 10 else str(i)
        
        index = "{:02d}".format(i)
        bucket.put_object(Body=img_data, ContentType='image/png', Key= gribGroundTruthsPath+index+"_"+datetime_str) #Key="test-predictions/mrms_grib/" +  "_"+index_str)

    # prediction functions:
    def load_module(self,input_height, input_width):
        """Load a TF-Hub snapshot of the 'Generative Method' model."""
        hub_module = tensorflow_hub.load(
            os.path.join(TFHUB_BASE_PATH, f"{input_height}x{input_width}"))
        # Note this has loaded a legacy TF1 model for running under TF2 eager mode.
        # This means we need to access the module via the "signatures" attribute. See
        # https://github.com/tensorflow/hub/blob/master/docs/migration_tf2.md#using-lower-level-apis
        # for more information.
        return hub_module.signatures['default']

    def predict(self,module, input_frames, num_samples=1,
                include_input_frames_in_result=False):
        """Make predictions from a TF-Hub snapshot of the 'Generative Method' model.

        Args:
            module: One of the raw TF-Hub modules returned by load_module above.
            input_frames: Shape (T_in,H,W,C), where T_in = 4. Input frames to condition
            the predictions on.
            num_samples: The number of different samples to draw.
            include_input_frames_in_result: If True, will return a total of 22 frames
            along the time axis, the 4 input frames followed by 18 predicted frames.
            Otherwise will only return the 18 predicted frames.

        Returns:
            A tensor of shape (num_samples,T_out,H,W,C), where T_out is either 18 or 22
            as described above.
        """
        input_frames = tf.math.maximum(input_frames, 0.)
        # Add a batch dimension and tile along it to create a copy of the input for
        # each sample:
        input_frames = tf.expand_dims(input_frames, 0)
        input_frames = tf.tile(input_frames, multiples=[num_samples, 1, 1, 1, 1])

        # Sample the latent vector z for each sample:
        _, input_signature = module.structured_input_signature
        z_size = input_signature['z'].shape[1]
        z_samples = tf.random.normal(shape=(num_samples, z_size))

        inputs = {
            "z": z_samples,
            "labels$onehot" : tf.ones(shape=(num_samples, 1)),
            "labels$cond_frames" : input_frames
        }
        samples = module(**inputs)['default']
        if not include_input_frames_in_result:
            # The module returns the input frames alongside its sampled predictions, we
            # slice out just the predictions:
            samples = samples[:, NUM_INPUT_FRAMES:, ...]

        # Take positive values of rainfall only.
        samples = tf.math.maximum(samples, 0.)
        return samples

    def extract_input_and_target_frames(self,radar_frames):
        """Extract input and target frames from a dataset row's radar_frames."""
        # We align our targets to the end of the window, and inputs precede targets.
        input_frames = radar_frames[-NUM_TARGET_FRAMES-NUM_INPUT_FRAMES : -NUM_TARGET_FRAMES]
        target_frames = radar_frames[-NUM_TARGET_FRAMES : ]
        return input_frames, target_frames

    def horizontally_concatenate_batch(self,samples):
        n, t, h, w, c = samples.shape
        # N,T,H,W,C => T,H,N,W,C => T,H,N*W,C
        return tf.reshape(tf.transpose(samples, [1, 2, 0, 3, 4]), [t, h, n*w, c])