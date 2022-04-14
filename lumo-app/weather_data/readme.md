## `ca_gov_downloader`
* This downloads hourly historical weather conditions from the canadian government
* This creates `tmp/ca_gov_data` and saves them there
* The file names correspond to `yyyy-mm.csv`. For example: `2019-03.csv`

## `ca_gov_uploader`
* This reads csv files from `tmp/ca_gov_data`, formats them into json, and uploads them to S3
* The bucket this uses is `lumo-app` in `us-east-1`
* The file names this uploads correspond to: `yyyy-mm-ddThh:mm:ssZ` (ISO-8601). For example: `2019-03-04T14:32:45Z`
* Note: the times are in UTC. **NOT LOCAL TO THE WEATHER STATION, NOT EST. UTC**

## `open_weather_map_testing`
* This was an attempt at using OWM, but OWM doesn't have precipitation data

## `archived_radar_data.py`
* Hourly mrms data from some archive
* Stored in `tmp/yyyy/mm/dd/hh-radar.grib2.gz`
* Not sure what timezone these are in

## `live_radar_data.py`
* Most recent mrms data from the noaa
* Stored in `tmp/yyyy/mm/dd/hhmm-radar.grib2.gz`
* Not sure what timezone these are in
