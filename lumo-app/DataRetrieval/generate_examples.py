import os
import re
from goes_py.GoesData import GoesData
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
from pathlib import Path
from Plot import Plot
import numpy as np
import math
import io
import boto3
import sys
sys.path.append('../Nowcasting')
from GoesPrediction import GoesPrediction

def generate_goes_examples(tfrecord_path, module, gt_arr):
    prediction = GoesPrediction(tfrecord_path)
    
    row = next(iter(prediction.reader()))
    radar, scaled_radar, cpt_path = prediction.convert_sat_to_radar(row)

    cmap = LinearSegmentedColormap('cpt', prediction.loadCPT(Path(cpt_path)))
    latlong_bbox = [row['lonmin'].numpy(), row['lonmax'].numpy(), row['latmin'].numpy(), row['latmax'].numpy()]
    xy_bbox = [row['lonmin_xy'].numpy(), row['lonmax_xy'].numpy(), row['latmin_xy'].numpy(), row['latmax_xy'].numpy()]
    band = row['band'].numpy().decode("utf-8")

    samples = prediction.predict(module, scaled_radar[:4],
                    num_samples=1, include_input_frames_in_result=False)
    
    rescaled_sat = prediction.convert_radar_to_sat(band, np.array(samples[0]), radar)

    filtered_sat = rescaled_sat[::2, ...]
 
    prediction.save_animation(field=filtered_sat, latlong_bbox=latlong_bbox, xy_bbox=xy_bbox, cmap=cmap, end_timestamp=row["end_time_timestamp"], band=band, is_example=True)
    rmse = generate_rmse(gt_arr, filtered_sat, band)
    plot_rmse(rmse, band, gt_arr.shape[0])
    return filtered_sat

def generate_rmse(gt_arr, pred_arr, band):
    rmse = np.empty(gt_arr.shape[0])
    for frame in range(gt_arr.shape[0]):
        rmse[frame] = 0
        for i in range(gt_arr.shape[1]):
            for j in range(gt_arr.shape[2]):
                rmse[frame] += (pred_arr[frame, i, j] - gt_arr[frame, i, j]) * (pred_arr[frame, i, j] - gt_arr[frame, i, j])
        rmse[frame] /= gt_arr.shape[1] * gt_arr.shape[2]
        rmse[frame] = math.sqrt(rmse[frame])

    return rmse

def plot_rmse(rmse_arr, band, num_frames):
    s3_client = boto3.client( 's3',
                aws_access_key_id="",
                aws_secret_access_key="",
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
    plt.plot(np.arange(1, num_frames + 1) * 10, rmse_arr, c="#F9C80E")
    plt.scatter(np.arange(1, num_frames + 1)  * 10, rmse_arr, c="#5DA9E9")

    img_data = io.BytesIO()
    fig.savefig(img_data, format='png', bbox_inches='tight')
    img_data.seek(0)
        
    session = boto3.Session(
        aws_access_key_id="",
        aws_secret_access_key="",
    )
    s3 = session.resource('s3')
    bucket = s3.Bucket("lumo-app")
    bucket.put_object(Body=img_data, ContentType='image/png', Key="examples/rmse/C" + band + "/" + "rmse_plot")

    plt.close()

if __name__ == "__main__":
    band_list = ["07", "08", "09", "10", "13", "14"]
    module = GoesPrediction.load_module("../Nowcasting/tfhub_snapshots/", 256, 256)

    for band in band_list:
        path = "/Users/saile/Documents/GOES/20220314/C" + band + "/"
        directory = os.listdir(path)
        dir_str = (' ').join(directory)        
        cmip_pattern = re.compile(r'OR_ABI-L2-CMIPF-M6C\w*\.nc') # old convention of datetime

        imgs_to_compare = np.empty((0, 256, 256, 1))
        arr = []
        for i, file_name in enumerate(re.findall(cmip_pattern, dir_str)):
            print(Path(path + file_name), i, len(re.findall(cmip_pattern, dir_str)))
            
            if (i >= len(re.findall(cmip_pattern, dir_str)) - 9): # save only the 9 ground truths to match prediction
                goesData = GoesData(Path(path + file_name), 'CMI', [-156.2995, 6.2995, -81.3282, 81.3282], 1)

                crop = goesData.generate_latlong_crop(cropsize=256,lat=40,long=-84)[0]
                
                goesData.save_crop(crop, True)
                print("converted i ", i)
                goes_img = np.expand_dims(crop.img, axis=2)
                imgs_to_compare = np.append(imgs_to_compare, np.expand_dims(goes_img, axis=0), axis=0)
                print(imgs_to_compare.shape)
                    
            elif (i >= len(re.findall(cmip_pattern, dir_str)) - 13 and i < len(re.findall(cmip_pattern, dir_str)) - 9):
                print("predicted i ", i)
                goesData = GoesData(Path(path + file_name), 'CMI', [-156.2995, 6.2995, -81.3282, 81.3282], 1)
                crop = goesData.generate_latlong_crop(cropsize=256,lat=40,long=-84)[0]
                crop.img = np.expand_dims(crop.img, axis=2)
                arr.append(crop)
                if (len(arr) == 4):
                    goes_plot = Plot("") # create Plot instance
                    tf_path = "C:/Users/saile/Documents/GOES/output/2022-03-06/C" + band + "/"
                    Path(tf_path).mkdir(parents=True, exist_ok=True)
                    goes_plot.save_as_tfrecord(tf_path + "rmse", arr)

        generate_goes_examples("C:/Users/saile/Documents/GOES/output/2022-03-14/C" + band , module, imgs_to_compare) # 24 images
        