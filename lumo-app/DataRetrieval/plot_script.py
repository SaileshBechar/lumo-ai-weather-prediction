from Plot import Plot
from datetime import date, timedelta

def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

goes_plot = Plot("/Users/saile/Documents/GOES/") # create Plot instance

start_date = date(2022, 3, 14) # YYYY/MM/DD
end_date = date(2022, 3, 15)

band_list = ["07", "08", "09", "10", "13", "14"]
for single_date in daterange(start_date, end_date):
    for band in band_list:
        goes_plot.download_images('CMIPF', single_date.strftime("%Y%m%d"), '190000', '211000', band)
        # goes_plot.decode_netCDF(single_date.strftime("%Y%m%d"), band=band , crop_size=256) # old convention of datetime
        # goes_plot.save_all_coverted_crops(num_frames=13)
    
