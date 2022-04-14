import requests
import os
from urllib.parse import urlparse
from pathlib import Path

# NOTE: I have no idea what timezone these dates & times are in

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

for year in range(2020, 2021 + 1):
    for month in range(1, 12 + 1):
        for day in range(1, 31 + 1):
            path = os.path.join(os.getcwd(), "tmp", f"{year}", f"{month:02}", f"{day:02}")
            os.makedirs(path, exist_ok=True)

            for hour in range(0, 23 + 1):
                url = f"https://mtarchive.geol.iastate.edu/{year}/{month:02}/{day:02}/mrms/ncep/RadarOnly_QPE_24H/RadarOnly_QPE_24H_00.00_{year}{month:02}{day:02}-{hour:02}0000.grib2.gz"
                print(f"Downloading {year}-{month:02}-{day:02}-{hour:02}")
                download(url, f"tmp/{year}/{month:02}/{day:02}/{hour:02}-radar.grib2.gz")
