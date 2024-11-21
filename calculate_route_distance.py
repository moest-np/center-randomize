import requests
from typing import Dict, List
import csv
import random
import math

distanceMatrixAPIKey = "SnWswgHwafCJDGDCYI6esdDC1iX2nBt3C0UWt7y1K4qiHeFpaim75dVAQTZD0Dfa"  # demo api key
PREF_DISTANCE_THRESHOLD = 2


def read_tsv(file_path: str) -> List[Dict[str, str]]:  # read the tsv file
    """
    Function to read the tsv file for school.tsv and centers.tsv
    Return a list of schools/centers as dicts.
    """
    data = []
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            data.append(dict(row))
    return data


def school_sort_key(s):
    # intent: allocate students from schools with large students count first
    # to avoid excessive fragmentation
    return (-1 if int(s['count']) > 500 else 1) * random.uniform(1, 100)


def append_row_to_tsv(row_data):  # append the row to the tsv file
    # Open the TSV file in append mode and create a csv writer object
    file_path = "./results/distance.tsv"
    with open(file_path, 'a', newline='', encoding='utf-8') as tsv_file:
        writer = csv.writer(tsv_file, delimiter='\t')

        # Write the row data to the TSV file
        writer.writerow(row_data)


def haversine_distance(lat1, lon1, lat2, lon2):  # calculate haversine distance
    """
    Calculate the great circle distance between two points
    on the earth specified in decimal degrees
    - Reference: https://en.wikipedia.org/wiki/Haversine_formula
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * \
        math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    radius_earth = 6371    # Average Radius of Earth in km
    distance = radius_earth * c
    return distance


# calculate route distance using distancematrix api, considers driving as means of transit
def calculate_route_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the best route distance between two points in driving mode in meters
    - Reference: https://distancematrix.ai/
    """

    # distancematrix.ai url
    url = f"https://api-v2.distancematrix.ai/maps/api/distancematrix/json?origins={
        lat1},{lon1}&destinations={lat2},{lon2}&key={distanceMatrixAPIKey}"

    try:
        response = requests.get(url)
        if "limit exceeded" in response.text:
            print("API limit exceeded")
            exit(1)
        else:
            distance = response.json(
                # converting to km
            )['rows'][0]['elements'][0]['distance']['value'] / 1000

        return distance
    except Exception as e:
        print(e)
        return 99999999  # 8(9s) to indicate error


schools = sorted(
    read_tsv("./sample_data/schools_grade12_2081.tsv"), key=school_sort_key)
centers = read_tsv("./sample_data/centers_grade12_2081.tsv")

for s in schools:
    school_lat = s.get('lat')
    school_long = s.get('long')
    if len(school_lat) == 0 or len(school_long) == 0:
        continue

    for c in centers:
        if s['scode'] == c['cscode']:
            distance = 0
            append_row_to_tsv([s['scode'], c['cscode'], distance])
            continue

        haversine_distance = haversine_distance(float(school_lat), float(  # calculating haversine distance to filter out the centers that are far away
            school_long), float(c.get('lat')), float(c.get('long')))
        if haversine_distance <= PREF_DISTANCE_THRESHOLD:
            distance = calculate_route_distance(float(school_lat), float(  # calculating route distance for the centers that are near
                school_long), float(c.get('lat')), float(c.get('long')))

            append_row_to_tsv([s['scode'], s['name-address'],  # appending the row to the TSV file
                               c['cscode'], c['name'], distance])
