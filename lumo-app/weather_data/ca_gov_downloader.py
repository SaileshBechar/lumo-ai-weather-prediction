import requests
import os
from urllib.parse import urlparse

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
                    for chunk in response.iter_content(chunk_size=1024*1024): # 1MB chunks
                        out_file.write(chunk)
                return file_path
        except Exception as ex:
            print(f'Attempt #{attempt} failed with error: {ex}')
    return ''

station_id = 48569

# These are inclusive
start_year = 2019
end_year = 2020

os.makedirs(os.path.dirname("tmp/ca_gov_data/"), exist_ok=True)

for year in range(start_year, end_year + 1):
    for month in range(1, 12 + 1):
        url = f"https://climate.weather.gc.ca/climate_data/bulk_data_e.html?format=csv&stationID={station_id}&Year={year}&Month={month}&Day=14&timeframe=1&time=UTC&submit= Download+Data"
        print(f"Downloading {year}-{month:02}")
        download(url, f"tmp/ca_gov_data/{year}-{month:02}.csv")


