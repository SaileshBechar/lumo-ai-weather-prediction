import numpy as np

class GoesImage:
    def __init__(self, img, band, date, timestamp, latlong_box, xy_box):
        self.img = img
        self.band = str(band) if (band >= 10) else f'0{str(band)}'
        self.date = date
        self.timestamp = timestamp
        self.latlong_box = latlong_box
        self.xy_box = xy_box
        self.num_bands = 1
    
    def get_latlong(self):
        return str(self.latlong_box[0]) + "_" + str(self.latlong_box[1]) + "_" + str(self.latlong_box[2]) + "_" + str(self.latlong_box[3])

    def concat_imgs_with_shared_timestamp(self, goes_image):
        print("ERROR!!! SHOULD NEVER BE CALLED")
        if (self.date == goes_image.date and str(self.timestamp)[:-6] == str(goes_image.timestamp)[:-6] and goes_image.band[0] not in self.band):
            self.img = np.append(self.img, np.expand_dims(goes_image.img, axis=2), axis=2)
            self.num_bands += 1
            self.band += "_" + str(goes_image.band) if (goes_image.band >= 10) else "0" + str(goes_image.band)

    def __str__(self):
        return f'Band:{self.band}, Date:{self.date}, Timestamp:{self.timestamp}, LatLong Box:{self.latlong_box}'
    
