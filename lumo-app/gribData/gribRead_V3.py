
import numpy as np, sys, os
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import xarray as xr
import netCDF4 as nc
#conda install -c conda-forge iris
#conda install -c conda-forge pynio
test = "./test/MRMS_RadarOnly_QPE_24H_00.00_20220107-230000.grib2"
#f = nio.open_file(filename)
#ds = xr.open_dataset(test, engine="pynio")
fn = './netcdf_file.nc'
ds = nc.Dataset(fn)
print(ds)
print(ds.__dict__)
print('keys')
with xr.open_dataset(fn) as d :
    print(d.keys())

print('test')
print(ds.unknown.data)
#iris.save(cubes[0],'input.nc')  # save a specific variable to grib 