# -*- coding: utf-8 -*-
"""Untitled3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Re6P6V7ikV__ldeLdPwRgApYb6mWlPkE
"""

import gzip
import shutil
import matplotlib.pyplot as plt
import numpy as np
import gzip
import shutil
import xarray as xr
# conda install -c conda-forge cfgrib
# conda install -c conda-forge pygrib=2.0.1

import matplotlib.pyplot as plt
import matplotlib.colors as colors
from mpl_toolkits.basemap import Basemap
from mpl_toolkits.basemap import shiftgrid
import numpy as np

#pip install pygrib

#https://stackoverflow.com/questions/68938395/python-decoding-ndfd-grib-binary-file-similar-to-writing-then-reading-the-file-u
file_content =''
#with gzip.open('./RadarOnly_QPE_24H_00.00_20210101-000000.grib2.gz', 'rb') as f_in:
with gzip.open('./RadarOnly_QPE_24H_00.00_20210101-010000.grib2.gz', 'rb') as f_in:
  with open('./file.grib2', 'wb') as f_out:
    shutil.copyfileobj(f_in, f_out)

import pygrib
#pip install pyproj
# conda install -c conda-forge pygrib=2.0.1
gr = pygrib.open('./test/MRMS_RadarOnly_QPE_24H_00.00_20220107-230000.grib2')
print(gr)


grb = gr.select()[0]
print(grb)
data = grb.values
print(data) 


lons = np.linspace(float(grb['longitudeOfFirstGridPointInDegrees']), \
float(grb['longitudeOfLastGridPointInDegrees']), int(grb['Ni']) )
lats = np.linspace(float(grb['latitudeOfFirstGridPointInDegrees']), \
float(grb['latitudeOfLastGridPointInDegrees']), int(grb['Nj']) )
#data, lons = shiftgrid(180., data, lons, start=False)
print("post ")
print(data)
print(lons)
print('here')
print(grb['longitudeOfFirstGridPointInDegrees'])
print(grb['Nj'])

for g in gr:
    print (g)

#for g in gr:
#  print (g.typeOfLevel, g.level, g.name, g.validDate, g.analDate, g.forecastTime)
 

grid_lon, grid_lat = np.meshgrid(lons, lats) #regularly spaced 2D grid
 
m = Basemap(projection='cyl', llcrnrlon=-180, \
    urcrnrlon=180.,llcrnrlat=lats.min(),urcrnrlat=lats.max(), \
    resolution='c')
 
x, y = m(grid_lon, grid_lat)
 
cs = m.pcolormesh(x,y,data,shading='nearest',cmap=plt.cm.gist_stern_r)
 
m.drawcoastlines()
m.drawmapboundary()
m.drawparallels(np.arange(-90.,120.,30.),labels=[1,0,0,0])
m.drawmeridians(np.arange(-180.,180.,60.),labels=[0,0,0,1])
 
plt.colorbar(cs,orientation='vertical', shrink=0.5)
plt.title('CAMS AOD forecast') # Set the name of the variable to plot
plt.savefig( 'test.png') # Set the output file name
