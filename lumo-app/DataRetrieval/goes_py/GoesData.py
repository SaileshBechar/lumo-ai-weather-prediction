from datetime import datetime
import numpy as np
import colorsys
from GoesImage import GoesImage
import xarray
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import LinearSegmentedColormap # Linear interpolation for color maps
import  matplotlib.patches as mpatches
from pathlib import Path
import metpy
from pyproj import Proj
import boto3
import io

class GoesData(object):
    """docstring for goes_data."""

    def __init__(self, filename, variable_to_plot, extent, resolution_of_plot):
        self.filename = filename
        self.x_points = None
        self.y_points = None
        self.resolution_of_plot = resolution_of_plot
        self.variable_to_plot = variable_to_plot
        self.goes_sat_data = None
        self._cmap_to_goes_plot_IR = Path(__file__).parent.resolve() / Path('IR4AVHRR6.cpt')
        self._cmap_to_goes_plot_WV = Path(__file__).parent.resolve() / Path('WVCOLOR35.cpt')
        self._cmap_convert_cpt = None
        self._cmap = None
        self.states_provinces = None
        self.geopolitics_boundaries = None
        self.extent_of_plot = {'lonmin':extent[0], 'lonmax':extent[1],
                               'latmin':extent[2], 'latmax':extent[3]}
        self.extent_of_crop = {'lonmin': -68, 'latmin': 71}
        self.crop_px = 256
        self.img_px_height = self.crop_px * 1
        self.img_px_width = self.crop_px * 1
        self.start_x_crop = 2945
        self.start_y_crop = 5079
        self._cartopy_projection = ccrs.PlateCarree()
        self._satelite_projection = None
        self.variable_to_plot_data = None
        ax = None
        self.figure = None
        self.datetime = None

    def _generate_cmap(self, band):
        if band >= 8 and band <= 10:
            self._cmap_convert_cpt = self.loadCPT(self._cmap_to_goes_plot_WV)
        else:    
            self._cmap_convert_cpt = self.loadCPT(self._cmap_to_goes_plot_IR)
        self._cmap = LinearSegmentedColormap('cpt', self._cmap_convert_cpt)

    def read_satelite_data(self):
        self.goes_sat_data = xarray.open_dataset(self.filename)

    def _get_GRIB_attributes(self):
        self.datetime = str(self.goes_sat_data.coords['time'].data)[:-3] + 'Z'
        self.band = 0

    def _get_attributes(self):
        self.datetime= self.goes_sat_data.attrs['date_created']
        self.scene_id = self.goes_sat_data.attrs['scene_id']
        self.band = self.goes_sat_data.coords['band_id'].data[0]
    
    def get_variable_to_plot_GRIB(self):
        try:
            self.variable_to_plot_data = self.goes_sat_data[self.variable_to_plot].data
            self.x_points = self.goes_sat_data[self.variable_to_plot].latitude.data
            self.y_points = self.goes_sat_data[self.variable_to_plot].longitude.data
        except KeyError as msg:
            print("GRIB Variable name may be not correct")
            exit()

    def get_variable_to_plot(self):
        try:
            self.variable_to_plot_data = self.goes_sat_data[self.variable_to_plot].data
            self.variable_plot = self.goes_sat_data.metpy.parse_cf(self.variable_to_plot)
            self.variable_goes_to_projection = self.variable_plot.metpy.cartopy_crs
        except KeyError as msg:
            print("Variable name may be not correct")
            exit()

    def _get_coordinates_from_goes_satelite(self):
        self.x_points = self.variable_plot.x
        self.y_points = self.variable_plot.y  

    def latlong_to_pixel(self, img):
        ''' This function does not work since assumes points are on flat surface '''
        long_conv = img.shape[1] / (self.extent_of_plot['lonmax'] - self.extent_of_plot['lonmin'])
        lat_conv = img.shape[0] / (self.extent_of_plot['latmax'] - self.extent_of_plot['latmin'])
        print(f' conv {lat_conv} {long_conv}')
        long_diff = self.extent_of_crop['lonmin'] - self.extent_of_plot['lonmin']
        lat_diff = self.extent_of_crop['latmin'] - self.extent_of_plot['latmin']
        x_pixels = int(long_diff * long_conv)
        y_pixels = int(lat_diff * lat_conv)
        print(x_pixels, y_pixels)

        return [y_pixels - self.img_px_height, y_pixels, x_pixels - self.img_px_width, x_pixels]

    def get_crops_from_image(self, img):
        crops = []
        right_x = self.start_x_crop
        top_y = self.start_y_crop
        left_x = right_x - self.crop_px
        bot_y = top_y - self.crop_px
        date = datetime.strptime(self.datetime, "%Y-%m-%dT%H:%M:%S.%fZ")
        
        concat_img = np.zeros(np.array(self.variable_to_plot_data).shape)
        for y in range(self.img_px_height // self.crop_px):
            for x in range(self.img_px_width // self.crop_px):
                temp_img = GoesImage(img[bot_y:top_y, left_x:right_x], self.band, date.strftime("%Y-%m-%d"), date.timestamp(), [left_x, right_x, bot_y, top_y])
                crops.append(temp_img)
                concat_img[bot_y:top_y, left_x:right_x] = img[bot_y:top_y, left_x:right_x]
                right_x = left_x
                left_x -= self.crop_px
            right_x = self.start_x_crop
            left_x = right_x - self.crop_px
            top_y = bot_y
            bot_y -= self.crop_px
            self.plot(concat_img)

        return crops

    def get_crop_from_latlong(self, img, bbox, latlong_bbox, xy_bbox):
        crops = []

        left_x = bbox[0]
        right_x = bbox[1]
        top_y = bbox[3]
        bot_y = bbox[2]
        date = datetime.strptime(self.datetime, "%Y-%m-%dT%H:%M:%S.%fZ")
        
        # print(right_x - left_x, bot_y - top_y)
        concat_img = np.zeros(np.array(self.variable_to_plot_data).shape)
        goesImg = GoesImage(img[top_y:bot_y, left_x:right_x], self.band, date.strftime("%Y-%m-%d"), date.timestamp(), latlong_bbox, xy_bbox)
        crops.append(goesImg)
        concat_img[top_y:bot_y, left_x:right_x] = img[top_y:bot_y, left_x:right_x]

        # self.plot(concat_img)

        return crops

    def plot(self, img):
        self.figure = plt.figure(figsize=(12, 12))
        ax = plt.axes(projection=self._cartopy_projection)

        ax.set_extent([self.extent_of_plot['lonmin'], self.extent_of_plot['lonmax'],
                              self.extent_of_plot['latmin'], self.extent_of_plot['latmax']],
                              crs=self._cartopy_projection)

        ax.imshow(img, origin='upper',
                extent=(self.x_points.min(), self.x_points.max(), self.y_points.min(), self.y_points.max()),
                transform=self.variable_goes_to_projection,
                interpolation='none', cmap=self._cmap, vmin=170, vmax=378)
        
        ''' custom shapeline has a bug on cartopy, don't use it '''
        states = cfeature.NaturalEarthFeature(category='cultural', scale='50m', facecolor='none',
                            name='admin_1_states_provinces_shp')
        # add the geographic boundaries
        l = cfeature.NaturalEarthFeature(category='cultural', name='admin_0_countries', scale='50m', facecolor='none')
        ax.add_feature(l, edgecolor='black', linewidth=0.25)
        plt.show()

    def save_crop(self, goes_img, is_example = False):
        fig = plt.figure(figsize=(10, 10))
        s3_prefix = "examples/" if is_example else "" 

        map_extent = goes_img.latlong_box
        img_extent = goes_img.xy_box

        ax = plt.axes(projection=self._cartopy_projection)
        ax.set_extent(map_extent, crs=self._cartopy_projection)

        # add the geographic boundaries
        countries = cfeature.NaturalEarthFeature(category='cultural', name='admin_0_countries', scale='50m', facecolor='none')
        lakes = cfeature.NaturalEarthFeature('physical', 'lakes', '10m')
        ax.add_feature(countries, edgecolor='black', linewidth=0.25)
        ax.add_feature(lakes, edgecolor='black', linewidth=0.25)

        waterloo = mpatches.Circle((-80.516670, 43.466667), 0.085, linestyle='solid', edgecolor='black', facecolor='gold')
        ax.add_patch(waterloo)
        big_loo = mpatches.Circle((-80.516670, 43.466667), 0.14, linestyle='solid', edgecolor='gold', facecolor='none')
        ax.add_patch(big_loo)

        
        ax.imshow(goes_img.img, origin='upper',
                    extent=img_extent,
                    transform=self.variable_goes_to_projection,
                    interpolation='none', cmap=self._cmap, vmin=170, vmax=378)

        
        img_data = io.BytesIO()
        fig.savefig(img_data, format='png', bbox_inches='tight')
        img_data.seek(0)
            
        session = boto3.Session(
            aws_access_key_id="",
            aws_secret_access_key="",
        )
        s3 = session.resource('s3')
        bucket = s3.Bucket("lumo-app")
        
        datetime_str = datetime.utcfromtimestamp(goes_img.timestamp).strftime("%Y-%m-%d-%H%M")
        bucket.put_object(Body=img_data, ContentType='image/png', Key=s3_prefix + "ground-truths/C" + goes_img.band + "/" + datetime_str)
        
        plt.close()

    def generate_crops_from_GRIB(self, filepath):
        self.read_satelite_data()
        self.get_variable_to_plot_GRIB()
        self._get_GRIB_attributes()
        self._generate_cmap(self.band)
        
        crops = self.get_crops_from_image(np.array(self.variable_to_plot_data))
        return crops

    def generate_crops(self, crop_size=256):
        self.read_satelite_data()
        self.get_variable_to_plot()
        self._get_attributes()
        self._generate_cmap(self.band)
        self._get_coordinates_from_goes_satelite()

        self.crop_px = crop_size
        self.img_px_height = self.crop_px * 1 # height is multiples of crops
        self.img_px_width = self.crop_px * 1 # width is multiples of crops

        crops = self.get_crops_from_image(np.array(self.variable_to_plot_data))

        return crops

    def generate_latlong_crop(self, cropsize, lat, long):
        self.read_satelite_data()
        self.get_variable_to_plot()
        self._get_attributes()
        self._generate_cmap(self.band)
        self._get_coordinates_from_goes_satelite()

        x = self.goes_sat_data[self.variable_to_plot].x.data
        y = self.goes_sat_data[self.variable_to_plot].y.data
        satHeight = self.goes_sat_data.data_vars['goes_imager_projection'].perspective_point_height
        satLon = self.goes_sat_data.data_vars['goes_imager_projection'].longitude_of_projection_origin
        satSweep = self.goes_sat_data.data_vars['goes_imager_projection'].sweep_angle_axis

        X = x[:]*satHeight
        Y = y[:]*satHeight
        X, Y = np.meshgrid(X, Y)

        proj = Proj(proj='geos', h=satHeight, lon_0=satLon, sweep=satSweep)
        Lons, Lats = proj(X, Y, inverse=True)
        Lons = np.where((Lons>=-360.0)&(Lons<=360.0)&(Lats>=-90.0)&(Lats<=90.0),Lons,-999.99)
        Lats = np.where((Lons>=-360.0)&(Lons<=360.0)&(Lats>=-90.0)&(Lats<=90.0),Lats,-999.99)
        
        left_x, bot_y = self.find_pixel_of_coordinate(Lons, Lats, long, lat)
        right_x, top_y = self.find_pixel_of_coordinate(Lons, Lats, Lons[bot_y - cropsize, left_x + cropsize], Lats[bot_y - cropsize, left_x + cropsize])

        crops = self.get_crop_from_latlong(
            np.array(self.variable_to_plot_data), 
            bbox=[left_x, right_x, bot_y, top_y], 
            latlong_bbox=[long, Lons[bot_y - cropsize, left_x + cropsize], lat, Lats[bot_y - cropsize, left_x + cropsize]],
            xy_bbox=[X[bot_y, left_x], X[top_y, right_x], Y[bot_y, left_x], Y[top_y, right_x]]
        )
        return crops
    
    def find_pixel_of_coordinate(self, Lons, Lats, long, lat):
        Dist = np.sqrt( (Lons-long)**2 + (Lats-lat)**2 )
        y, x = np.unravel_index( np.argmin(Dist, axis=None ), Dist.shape)
        return x, y

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