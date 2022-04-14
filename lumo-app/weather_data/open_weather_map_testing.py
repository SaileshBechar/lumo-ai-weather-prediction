import requests
import datetime
import pprint
import json

API_KEY = "505121894cf6d0b700415ea1fb337132"

# city_id = "Waterloo,ON,CA"
# longitude = "43.47290147661985"
# latitude = "-80.54493092329561"
city_id = "Toronto,CA"
start_date = datetime.datetime(2021, 1, 1, 0, 0).timestamp()
# end_date = datetime.datetime(2021, 11, 1, 0, 0).timestamp()

# url = f"http://history.openweathermap.org/data/2.5/history/city?q={city_id}&type=hour&start={start_date}&end={end_date}&appid={API_KEY}"
# url = f"http://history.openweathermap.org/data/2.5/history/city?q={city_id}&type=hour&start={start_date}&cnt={hours}&appid={API_KEY}"
# url = f"http://history.openweathermap.org/data/2.5/history/city?lat={latitude}&lon={longitude}&type=hour&start={start_date}&end={end_date}&appid={API_KEY}"


# pprint.pprint(r.json())

for day in range(0, 2):
    start_date = datetime.datetime(2021, 1, 1) + datetime.timedelta(day)
    url = f"http://history.openweathermap.org/data/2.5/history/city?q={city_id}&type=hour&start={start_date.timestamp()}&cnt=24&appid={API_KEY}"
    r = requests.get(url)
    json_data = r.json()
    with open(start_date.strftime("data_archive/%Y-%m-%d.txt"), "w+") as data_file:
        pprint.pprint(json_data["list"])
        # json.dump(json_data, data_file)

