import csv
import json
import os
from os import path

data_folder = "tmp/ca_gov_data"
os.makedirs(os.path.dirname("tmp/ca_gov_data/json/"), exist_ok=True)
files = [f for f in os.listdir(data_folder) if path.isfile(path.join(data_folder, f)) and f.endswith(".csv")]

for data_file in files:
    filepath = path.join(data_folder, data_file)
    with open(filepath, encoding="utf-8-sig") as csv_file:
        csv_data = csv.DictReader(csv_file)

        for row in csv_data:
            data = {}
            datetime_string = f"{row['Year']}-{row['Month']}-{row['Day']}T{row['Time (UTC)']}:00Z"
            data["datetime"] = datetime_string
            data["longitude"] = row["Longitude (x)"]
            data["latitude"] = row["Latitude (y)"]
            data["temperature"] = row[u"Temp (\N{DEGREE SIGN}C)"]
            data["precipitation_amount"] = row["Precip. Amount (mm)"]
            data["relative_humidity"] = row["Rel Hum (%)"]
            data["weather"] = None if row["Weather"] == "NA" else row["Weather"]

            with open(path.join(data_folder, "json/", datetime_string + ".json"), 'w') as out_file:
                json.dump(data, out_file)
