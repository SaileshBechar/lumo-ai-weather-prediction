import datetime
import os

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import animation
import numpy as np
import tensorflow as tf
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pyproj
import tensorflow_hub
import io
import boto3
import json

class GoesPrediction:
    def __init__(self, dataset_folder):
        matplotlib.rc('animation', html='jshtml')
        self.DATASET_ROOT_DIR = dataset_folder
        self._FEATURES = {name: tf.io.FixedLenFeature([], dtype)
                for name, dtype in [
                    ("radar", tf.string),
                    ("lonmin", tf.float32), ("lonmax", tf.float32),
                    ("latmin", tf.float32), ("latmax", tf.float32),
                    ("lonmin_xy", tf.float32), ("lonmax_xy", tf.float32),
                    ("latmin_xy", tf.float32), ("latmax_xy", tf.float32),
                    ("end_time_timestamp", tf.int64), ("band", tf.string),
                    ("num_frames", tf.int64), ("height", tf.int64),
                    ("width", tf.int64)
                ]}

        self.NUM_INPUT_FRAMES = 4 # Fixed values supported by the snapshotted model.
        self.NUM_TARGET_FRAMES = 18

    def parse_and_preprocess_row(self, row):
        result = tf.io.parse_single_example(row, self._FEATURES)
        shape = (result["num_frames"], result["height"], result["width"], 1)
        radar_bytes = result.pop("radar")
        
        radar_float64 = tf.reshape(tf.io.parse_tensor(radar_bytes, tf.float64), shape)
        radar_float32 = tf.cast(radar_float64, tf.float32) # needs to convert from double to float for prediction
        
        result["radar_frames"] = radar_float32
        return result

    def reader(self, variant=""):
        shards_glob = os.path.join(self.DATASET_ROOT_DIR + "/", "*.tfrecord.gz")
        print("glob",shards_glob)
        shard_paths = tf.io.gfile.glob(shards_glob)
        print(shard_paths)

        shards_dataset = tf.data.Dataset.from_tensor_slices(shard_paths)

        return (
        shards_dataset
        .interleave(lambda x: tf.data.TFRecordDataset(x, compression_type="GZIP"),
                    num_parallel_calls=tf.data.AUTOTUNE)
        .map(lambda row: self.parse_and_preprocess_row(row),
            num_parallel_calls=tf.data.AUTOTUNE)
        )

    def loadCPT(self, path):
        try:
            f = open(path)
        except:
            print ("File ", path, "not found")
            return None

        lines = f.readlines()

        f.close()

        x = np.array([])
        r = np.array([])
        g = np.array([])
        b = np.array([])

        colorModel = 'RGB'

        for l in lines:
            ls = l.split()
            if l[0] == '#':
                if ls[-1] == 'HSV':
                    colorModel = 'HSV'
                    continue
                else:
                    continue
            if ls[0] == 'B' or ls[0] == 'F' or ls[0] == 'N':
                pass
            else:
                x=np.append(x,float(ls[0]))
                r=np.append(r,float(ls[1]))
                g=np.append(g,float(ls[2]))
                b=np.append(b,float(ls[3]))
                xtemp = float(ls[4])
                rtemp = float(ls[5])
                gtemp = float(ls[6])
                btemp = float(ls[7])

            x=np.append(x,xtemp)
            r=np.append(r,rtemp)
            g=np.append(g,gtemp)
            b=np.append(b,btemp)

        if colorModel == 'HSV':
            for i in range(r.shape[0]):
                rr, gg, bb = colorsys.hsv_to_rgb(r[i]/360.,g[i],b[i])
            r[i] = rr ; g[i] = gg ; b[i] = bb

        if colorModel == 'RGB':
            r = r/255.0
            g = g/255.0
            b = b/255.0

        xNorm = (x - x[0])/(x[-1] - x[0])

        red   = []
        blue  = []
        green = []

        for i in range(len(x)):
            red.append([xNorm[i],r[i],r[i]])
            green.append([xNorm[i],g[i],g[i]])
            blue.append([xNorm[i],b[i],b[i]])

        colorDict = {'red': red, 'green': green, 'blue': blue}

        return colorDict

    def convert_sat_to_radar(self, row):
        radar = row["radar_frames"].numpy()
        band = row['band'].numpy().decode("utf-8")
        if (band == '07'):
            zero_indices = [ radar > 265 ]
            m = (12 - 0) / (212 - 265) # y2-y1/x2-x1
            b = 0 - (m * 212)
            scaled_radar = radar * m + b + 12
            scaled_radar[tuple(zero_indices)] = -1
            print(scaled_radar.min(), scaled_radar.max())
            return radar, scaled_radar, '../DataRetrieval/goes_py/IR4AVHRR6.cpt'
        elif (int(band) > 10):
            zero_indices = [ radar > 253 ]
            m = (12 - 0) / (205 - 253) # y2-y1/x2-x1
            b = 0 - (m * 205)
            scaled_radar = radar * m + b + 12
            scaled_radar[tuple(zero_indices)] = -1
            print(scaled_radar.min(), scaled_radar.max())
            return radar, scaled_radar, '../DataRetrieval/goes_py/IR4AVHRR6.cpt'
        else:
            flip_sat = radar * -1
            flip_sat = flip_sat + flip_sat.min()
            m = (15 - 0) / (flip_sat.max() - flip_sat.min()) # y2-y1/x2-x1
            b = 0 - (m * flip_sat.min())
            zero_indices = [flip_sat > flip_sat.max() - 5]
            scaled_radar = flip_sat * m + b
            scaled_radar[tuple(zero_indices)] = -1
            return radar, scaled_radar, '../DataRetrieval/goes_py/WVCOLOR35.cpt'

    def convert_radar_to_sat(self, band, sample, radar):
        if (band == '07'):
            zero_indices = [sample < sample.min() + 1] 
            
            m = (212 - 265) / (12 - 0)
            b = 265 - (m * (0))

            scaled_sat = sample * m + b
            scaled_sat[tuple(zero_indices)] = np.mean(radar[radar > 265])
            print(scaled_sat.min(), scaled_sat.max())
            return scaled_sat
        elif (int(band) > 10):
            zero_indices = [sample < sample.min() + 1] 
            
            m = (205 - 253) / (12 - 0)
            b = 253 - (m * (0))

            scaled_sat = sample * m + b
            scaled_sat[tuple(zero_indices)] = np.mean(radar[radar > 253])
            print(scaled_sat.min(), scaled_sat.max())
            return scaled_sat
        else:
            zero_indices = [sample < sample.min() + 1] # less than 1 equals background
        
            flip_radar = sample * -1
            
            m = (radar.max() - radar.min()) / (-1 - (-14.3))
            b = radar.min() - (m * -14.3)

            scaled_sat = flip_radar * m + b
            scaled_sat[tuple(zero_indices)] = radar.max() - 5
            return scaled_sat

    def plot_animation(self, field, figsize=None,
                    vmin=0, vmax=15, cmap='jet', **imshow_args):
        fig = plt.figure(figsize=figsize)
        ax = plt.axes()
        ax.set_axis_off()
        plt.close() # Prevents extra axes being plotted below animation
        img = ax.imshow(field[0, ...], cmap=cmap, **imshow_args)

        def animate(i):
            img.set_data(field[i, ...])
            return (img,)

        return animation.FuncAnimation(
            fig, animate, frames=field.shape[0], interval=24, blit=False)
    
    def plot_on_map(self, field, latlong_bbox, xy_bbox, cmap) :
        fig = plt.figure(figsize=(10, 10))
    
        region_extent = latlong_bbox
        img_extent = xy_bbox

        crs = ccrs.PlateCarree()
        ax = plt.axes(projection=crs)
        ax.set_extent(region_extent, crs=crs)

        waterloo = mpatches.Circle((-80.516670, 43.466667), 0.085, linestyle='solid', edgecolor='#766C7F', facecolor='#F9C80E')
        ax.add_patch(waterloo)
        big_loo = mpatches.Circle((-80.516670, 43.466667), 0.14, linestyle='solid', edgecolor='#F9C80E', facecolor='none')
        ax.add_patch(big_loo)
        
        transform = ccrs.Geostationary(central_longitude=-75.0, satellite_height=35786023.0, sweep_axis='x')
        
        img = ax.imshow(field, origin='upper',
                    extent=img_extent,
                    transform=transform,
                    interpolation='none', cmap=cmap, vmin=170, vmax=378)
        
        # add the geographic boundaries
        countries = cfeature.NaturalEarthFeature(category='cultural', name='admin_0_countries', scale='50m', facecolor='none')
        lakes = cfeature.NaturalEarthFeature('physical', 'lakes', '10m')
        ax.add_feature(countries, edgecolor='gold', linewidth=0.25)
        ax.add_feature(lakes, edgecolor='gold', linewidth=0.25)
        
        fig.colorbar(mappable=img, orientation="horizontal")
        plt.show()
    
    def plot_animation_on_map(self, field, latlong_bbox, xy_bbox, cmap):
        fig = plt.figure(figsize=(10, 10))

        transform = ccrs.Geostationary(central_longitude=-75.0, satellite_height=35786023.0, sweep_axis='x')
        map_extent = latlong_bbox
        img_extent = xy_bbox
        crs = ccrs.PlateCarree()
        ax = plt.axes(projection=crs)
        ax.set_extent(map_extent, crs=crs)
        
        # add the geographic boundaries
        countries = cfeature.NaturalEarthFeature(category='cultural', name='admin_0_countries', scale='50m', facecolor='none')
        lakes = cfeature.NaturalEarthFeature('physical', 'lakes', '10m')
        ax.add_feature(countries, edgecolor='gold', linewidth=0.25)
        ax.add_feature(lakes, edgecolor='gold', linewidth=0.25)
        
        
        ax.imshow(field[0, ..., 0], origin='upper',
                    extent=img_extent,
                    transform=transform,
                    interpolation='none', cmap=cmap, vmin=170, vmax=378)
        
        plt.close()
        
        def animate(i):
            return (ax.imshow(field[i, ..., 0], origin='upper',
                    extent=img_extent,
                    transform=transform,
                    interpolation='none', cmap=cmap, vmin=170, vmax=378)
        ,)

        return animation.FuncAnimation(
        fig, animate, frames=field.shape[0],
        interval=24, blit=False)

    def save_animation(self, field, latlong_bbox, xy_bbox, cmap, end_timestamp, band, is_example=False):
        s3_prefix = "examples/" if is_example else ""
        s3_client = boto3.client( 's3',
                aws_access_key_id="AKIAWRHKEEZVRHAQDW6L",
                aws_secret_access_key="JF3BJEi1FcBwEBaisIK5FAIOV9NzF83yEMEzQQoh",
                region_name="us-east-1"
            )
            
        response = s3_client.list_objects_v2(Bucket="lumo-app", Prefix=s3_prefix + "predictions/C" + band + "/")
        if 'Contents' in response:
            for object in response['Contents']:
                print('Deleting', object['Key'])
                s3_client.delete_object(Bucket="lumo-app", Key=object['Key'])
                    
        for i in range(field.shape[0]):
            fig = plt.figure(figsize=(10, 10))

            transform = ccrs.Geostationary(central_longitude=-75.0, satellite_height=35786023.0, sweep_axis='x')
            map_extent = latlong_bbox
            img_extent = xy_bbox
            crs = ccrs.PlateCarree()
            ax = plt.axes(projection=crs)
            ax.set_extent(map_extent, crs=crs)

            # add the geographic boundaries
            countries = cfeature.NaturalEarthFeature(category='cultural', name='admin_0_countries', scale='50m', facecolor='none')
            lakes = cfeature.NaturalEarthFeature('physical', 'lakes', '10m')
            ax.add_feature(countries, edgecolor='black', linewidth=0.25)
            ax.add_feature(lakes, edgecolor='black', linewidth=0.25)

            waterloo = mpatches.Circle((-80.516670, 43.466667), 0.085, linestyle='solid', edgecolor='#766C7F', facecolor='#F9C80E')
            ax.add_patch(waterloo)
            big_loo = mpatches.Circle((-80.516670, 43.466667), 0.14, linestyle='solid', edgecolor='#F9C80E', facecolor='none')
            ax.add_patch(big_loo)

            ax.imshow(field[i, ..., 0], origin='upper',
                        extent=img_extent,
                        transform=transform,
                        interpolation='none', cmap=cmap, vmin=170, vmax=378)
            
            img_data = io.BytesIO()
            fig.savefig(img_data, format='png', bbox_inches='tight', facecolor='#F9C80E')
            img_data.seek(0)
                
            session = boto3.Session(
                aws_access_key_id="AKIAWRHKEEZVRHAQDW6L",
                aws_secret_access_key="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",
            )
            s3 = session.resource('s3')
            bucket = s3.Bucket("lumo-app")
            
            datetime_str = datetime.datetime.utcfromtimestamp(end_timestamp).strftime("%Y-%m-%d-%H%M")
            index_str = f'0{str(i)}' if i < 10 else str(i)
            bucket.put_object(Body=img_data, ContentType='image/png', Key=s3_prefix + "predictions/C" + band + "/" + index_str + '_' + datetime_str)
            
            plt.close()

    def load_module(hub_path, input_height, input_width):
        """Load a TF-Hub snapshot of the 'Generative Method' model."""
        hub_module = tensorflow_hub.load(
            os.path.join(hub_path, f"{input_height}x{input_width}"))
        # Note this has loaded a legacy TF1 model for running under TF2 eager mode.
        # This means we need to access the module via the "signatures" attribute. See
        # https://github.com/tensorflow/hub/blob/master/docs/migration_tf2.md#using-lower-level-apis
        # for more information.
        return hub_module.signatures['default']


    def predict(self, module, input_frames, num_samples=1,
                include_input_frames_in_result=True):
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
            samples = samples[:, self.NUM_INPUT_FRAMES:, ...]

        # Take positive values of rainfall only.
        samples = tf.math.maximum(samples, 0.)
        return samples
    
    def generate_cloud_cover(self, pred_arr, datetime):
        top_y = 125 # specific starting point vals in goes crop
        left_x = 144
        px_offset = 16 # size of how large of area to analyze
        for frame in range(pred_arr.shape[0]):
            cloud_frame = pred_arr[frame, top_y:top_y + px_offset, left_x:left_x + px_offset, 0]
            partly_cloud_cover = cloud_frame[cloud_frame <= 253].shape[0] / (px_offset * px_offset)
            cloud_cover = cloud_frame[cloud_frame <= 246].shape[0] / (px_offset * px_offset)
            if (cloud_cover > 0.7):
                cloud_str = "cloud"
            elif (partly_cloud_cover > 0.7) :
                cloud_str = "partly"
            else:
                cloud_str = "sun"

            session = boto3.Session(
                aws_access_key_id="AKIAWRHKEEZVRHAQDW6L",
                aws_secret_access_key="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",
            )
            s3 = session.resource('s3')
            bucket = s3.Bucket("lumo-app")

            index_str = f'0{str(frame)}' if frame < 10 else str(frame)
            bucket.put_object(Body=json.dumps({"cloud_str":cloud_str}), ContentType="application/json", Key="cloud-cover/" + index_str + "_" + datetime)

    def generate_rainfall(pred_arr):
        top_y = 138 # specific starting point vals in goes crop
        left_x = 106
        px_offset = 32 # size of how large of area to analyze
        for frame in range(pred_arr.shape[0]):
            rain_frame = pred_arr[frame, top_y:top_y + px_offset, left_x:left_x + px_offset, 0]
            avg_rain_intensity = np.mean(rain_frame)
            rain_cover = rain_frame[rain_frame > 0.1].shape[0] / (px_offset * px_offset)
            print("There is a ", rain_cover * (0.89 - (frame*0.01)), " percent chance of ", avg_rain_intensity, " mm of rain")