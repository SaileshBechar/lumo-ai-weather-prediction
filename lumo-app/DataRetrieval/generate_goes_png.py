from goes_py.GoesData import GoesData
from pathlib import Path
import re
import os

def netCDF_to_PNG(filepath):
    goesData = GoesData(Path(filepath), 'CMI', [-156.2995, 6.2995, -81.3282, 81.3282], 1)

    crop = goesData.generate_latlong_crop(cropsize=256,lat=40,long=-84)[0]

    goesData.save_crop(crop, False)


if __name__ == "__main__":
    path = "/Users/saile/Documents/GOES/20220305/C07/"
    directory = os.listdir(path)
    dir_str = (' ').join(directory)        
    cmip_pattern = re.compile(r'OR_ABI-L2-CMIPF-M6C\w*\.nc') # old convention of datetime

    for file_name in re.findall(cmip_pattern, dir_str):
        print(Path(path + file_name))
        netCDF_to_PNG(Path(path + file_name))