from GoesPrediction import GoesPrediction
from matplotlib.colors import LinearSegmentedColormap 
from pathlib import Path
import numpy as np
import datetime

def generate_goes_prediction(tfrecord_path, module):
    prediction = GoesPrediction(tfrecord_path)
    
    row = next(iter(prediction.reader()))
    radar, scaled_radar, cpt_path = prediction.convert_sat_to_radar(row)

    cmap = LinearSegmentedColormap('cpt', prediction.loadCPT(Path(cpt_path)))
    latlong_bbox = [row['lonmin'].numpy(), row['lonmax'].numpy(), row['latmin'].numpy(), row['latmax'].numpy()]
    xy_bbox = [row['lonmin_xy'].numpy(), row['lonmax_xy'].numpy(), row['latmin_xy'].numpy(), row['latmax_xy'].numpy()]
    band = row['band'].numpy().decode("utf-8")

    # prediction.plot_on_map(field=scaled_radar, cmap=cmap, latlong_bbox=latlong_bbox, xy_bbox=xy_bbox)
    samples = prediction.predict(module, scaled_radar[:4],
                    num_samples=1, include_input_frames_in_result=False)
    
    rescaled_sat = prediction.convert_radar_to_sat(band, np.array(samples[0]), radar)

    prediction.save_animation(field=rescaled_sat, latlong_bbox=latlong_bbox, xy_bbox=xy_bbox, cmap=cmap, end_timestamp=row["end_time_timestamp"], band=band)

    if (band == "14"):
        prediction.generate_cloud_cover(rescaled_sat, datetime.datetime.utcfromtimestamp(row["end_time_timestamp"]).strftime("%Y-%m-%d-%H%M"))

if __name__ == "__main__":
    band_list = ["07", "08", "09", "10", "13", "14"]
    band_list = ["14"]
    module = GoesPrediction.load_module("./tfhub_snapshots/", 256, 256)
    for band in band_list:
        generate_goes_prediction("C:/Users/saile/Documents/GOES/output/2022-03-12/C" + band, module)