import os
import re
import requests
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path

# This was taken from https://stackoverflow.com/a/62743933
def download(url: str, file_path='', attempts=2):
    """Downloads a URL content into a file (with large file support by streaming)

    :param url: URL to download
    :param file_path: Local file name to contain the data downloaded
    :param attempts: Number of attempts
    :return: New file path. Empty string if the download failed
    """
    if not file_path:
        file_path = os.path.realpath(os.path.basename(url))
    url_sections = urlparse(url)
    if not url_sections.scheme:
        url = f'http://{url}'
    for attempt in range(1, attempts+1):
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                with open(file_path, 'wb') as out_file:
                    for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                        out_file.write(chunk)
                return file_path
        except Exception as ex:
            print(f'Attempt #{attempt} failed with error: {ex}')
    return ''

url = "https://mrms.ncep.noaa.gov/data/2D/RadarOnly_QPE_01H/"
response = requests.get(url)

latest_line = ""
for line in response.iter_lines():
    if "latest" in str(line):
        latest_line = str(line)

dt = re.search("\d{2}-\w{3}-\d{4} \d{2}:\d{2}", latest_line).group(0)

dt_obj = datetime.strptime(dt, "%d-%b-%Y %H:%M")

path = os.path.join(os.getcwd(), "tmp", f"{dt_obj.year}", f"{dt_obj.month:02}", f"{dt_obj.day:02}")
os.makedirs(path, exist_ok=True)

url = "https://mrms.ncep.noaa.gov/data/2D/RadarOnly_QPE_01H/MRMS_RadarOnly_QPE_01H.latest.grib2.gz"
print(f"Downloading {dt_obj.year}-{dt_obj.month:02}-{dt_obj.day:02}-{dt_obj.hour:02}{dt_obj.minute:02}")
download(url, f"tmp/{dt_obj.year}/{dt_obj.month:02}/{dt_obj.day:02}/{dt_obj.hour:02}{dt_obj.minute:02}-radar.grib2.gz")
