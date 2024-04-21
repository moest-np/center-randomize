import math
import csv
import random
import os
from typing import Dict, List

from settings import (DISTANCE_TSV, OUTPUT_DIR, 
                    PREF_DISTANCE_THRESHOLD, 
                    ABS_DISTANCE_THRESHOLD, 
                    MIN_STUDENT_IN_CENTER, 
                    PREF_CUTOFF,
                    STRETCH_CAPACITY_FACTOR,
                    PREFS_TSV, SCHOOLS_TSV,
                    CENTERS_TSV,OUTPUT_TSV,)


def create_dir(dirPath:str):
    """
    Create the given directory if it doesn't exists
    - Creates all the directories needed to resolve to the provided directory path
    """
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth specified in decimal degrees
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    radius_earth = 6371  # Radius of Earth in kilometers
    distance = radius_earth * c
    return distance

def centers_within_distance(school: Dict[str, str], centers: Dict[str, str], distance_threshold: float) -> List[Dict[str, any]]:
    """
    Return List of centers that are within given distance from school.
    If there are no centers within given distance return one that is closest
    Returned params :
            {'cscode', 'name', 'address', 'capacity', 'lat', 'long', 'distance_km'}

    """
    def center_to_dict(c, distance):
        return {'cscode': c['cscode'], 'name': c['name'], 'address': c['address'], 'capacity': c['capacity'], 'lat': c['lat'], 'long': c['long'], 'distance_km': distance}
    
    def sort_key(c):
        # intent: sort by preference score DESC then by distance_km ASC 
        # leaky abstraction - sorted requires a single numberic value for each element
        return c['distance_km'] * random.uniform(1,5) - get_pref(school['scode'], c['cscode'])*100
    
    school_lat = school.get('lat')
    school_long = school.get('long')
    if len(school_lat) == 0 or len(school_long) == 0:
        return []
    
    within_distance = []
    nearest_distance = None;
    nearest_center = None
    for c in centers: 
        distance = haversine_distance(float(school_lat), float(school_long), float(c.get('lat')), float(c.get('long')))
        if school['scode'] == c['cscode']:
            continue
        if nearest_center == None or distance < nearest_distance:
            nearest_center = c
            nearest_distance = distance

        if distance <= distance_threshold and get_pref(school['scode'], c['cscode']) > PREF_CUTOFF:
            within_distance.append(center_to_dict(c, distance))
            
    if len(within_distance) > 0:
        return sorted(within_distance, key=sort_key) 
    else: # if there are no centers within given  threshold, return one that is closest
        return [center_to_dict(nearest_center, nearest_distance)]

def read_tsv(file_path: str) -> List[Dict[str, str]]:
    data = []
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            data.append(dict(row))
    return data

def read_prefs(file_path: str) -> Dict[str, Dict[str, int]]:
    prefs = {}
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            if prefs.get(row['scode']):
                if prefs[row['scode']].get(row['cscode']):
                    prefs[row['scode']][row['cscode']] += int(row['pref'])
                else:
                    prefs[row['scode']][row['cscode']] = int(row['pref'])
            else:
                prefs[row['scode']] = {row['cscode']: int(row['pref'])}

    return prefs

def get_pref(scode, cscode) -> int:
    if prefs.get(scode):
        if prefs[scode].get(cscode):
            return prefs[scode][cscode]
        else:
            return 0
    else:
        return 0 

def calc_per_center(count: int) -> int: 
    if count <= 400:
        return 100
    # elif count <= 900:
    #     return 200
    else: 
        return 200

def school_sort_key(s):
    return (-1 if int(s['count']) > 500 else 1 ) * random.uniform(1, 100)

def allocate(scode:str, cscode:str, count: int):
    if allocations.get(scode) == None:
        allocations[scode] = {cscode: count}
    elif allocations[scode].get(cscode) == None:
        allocations[scode][cscode] = count
    else:
        allocations[scode][cscode] += count

def is_allocated(scode1: str, scode2:str) -> bool:
    if allocations.get(scode1):
        return allocations[scode1].get(scode2) != None
    else:
        return False

schools = sorted(read_tsv(SCHOOLS_TSV), key= school_sort_key)
centers = read_tsv(CENTERS_TSV)
centers_remaining_cap = {c['cscode']:int(c['capacity']) for c in centers}
prefs = read_prefs(PREFS_TSV)

remaining = 0 # stores count of non allocated students 
allocations = {}  # to track mutual allocations
create_dir(OUTPUT_DIR)
with open(DISTANCE_TSV, 'w', encoding='utf-8') as intermediate_file, \
open(OUTPUT_TSV, 'w', encoding='utf-8') as a_file:
    writer = csv.writer(intermediate_file, delimiter="\t")
    writer.writerow(["scode", "s_count", "school_name", "school_lat", "school_long", "cscode", "center_name", "center_address", "center_capacity", "distance_km"])
    
    allocation_file = csv.writer(a_file, delimiter='\t')
    allocation_file.writerow(["scode", "school", "cscode", "center", "center_address", "allocation", "distance_km"])
    
    for s in schools:
        centers_for_school = centers_within_distance(s, centers, PREF_DISTANCE_THRESHOLD)
        to_allot = int(s['count'])
        per_center = calc_per_center(to_allot)

        allocated_centers = {}

        # per_center = math.ceil(to_allot / min(calc_num_centers(to_allot), len(centers_for_school))) 
        for c in centers_for_school:
            writer.writerow([s['scode'], s['count'], s['name-address'], s['lat'], s['long'], c['cscode'], c['name'], c['address'], c['capacity'], c['distance_km'] ])
            if is_allocated(c['cscode'], s['scode']):
                continue
            next_allot = min(to_allot, per_center, max(centers_remaining_cap[c['cscode']], MIN_STUDENT_IN_CENTER))
            if to_allot > 0 and next_allot > 0 and centers_remaining_cap[c['cscode']] >= next_allot:
                allocated_centers[c['cscode']] = c
                allocate(s['scode'], c['cscode'], next_allot)
                # allocation.writerow([s['scode'], s['name-address'], c['cscode'], c['name'], c['address'], next_allot, c['distance_km']])
                to_allot -= next_allot
                centers_remaining_cap[c['cscode']] -= next_allot
        
        if to_allot > 0: # try again with relaxed constraints and more capacity at centers 
            expanded_centers = centers_within_distance(s, centers, ABS_DISTANCE_THRESHOLD)
            for c in expanded_centers:
                if is_allocated(c['cscode'], s['scode']):
                    continue
                stretched_capacity = math.floor(int(c['capacity']) * STRETCH_CAPACITY_FACTOR + centers_remaining_cap[c['cscode']])
                next_allot = min(to_allot, max(stretched_capacity, MIN_STUDENT_IN_CENTER))
                if to_allot > 0 and next_allot > 0 and stretched_capacity >= next_allot:
                    allocated_centers[c['cscode']] = c
                    allocate(s['scode'], c['cscode'], next_allot)
                    # allocation.writerow([s['scode'], s['name-address'], c['cscode'], c['name'], c['address'], next_allot, c['distance_km']])
                    to_allot -= next_allot
                    centers_remaining_cap[c['cscode']] -= next_allot

        for c in allocated_centers.values():
            allocation_file.writerow([s['scode'], s['name-address'], c['cscode'], c['name'], c['address'], allocations[s['scode']][c['cscode']], c['distance_km']])

        if to_allot > 0: 
            remaining+=to_allot
            print(f"{to_allot}/{s['count']} left for {s['scode']} {s['name-address']} centers: {len(centers_for_school)}")
                

    print("Remaining capacity at each center (remaining_capacity cscode):")
    print(sorted([(v,k) for k, v in centers_remaining_cap.items() if v != 0]))
    print(f"Total remaining capacity across all centers: {sum({k:v for k, v in centers_remaining_cap.items() if v != 0}.values())}")
    print(f"Students not assigned: {remaining}")

