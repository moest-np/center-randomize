OUTPUT_DIR = 'results/'

PREF_DISTANCE_THRESHOLD = 2  # Preferred threshold distance in kilometers
ABS_DISTANCE_THRESHOLD = 7  # Absolute threshold distance in kilometers
MIN_STUDENT_IN_CENTER = 10  # minimum number of students from a school to be assigned to a center in normal circumstances
STRETCH_CAPACITY_FACTOR = 0.02  # how much can center capacity be streched if need arises
PREF_CUTOFF = -4 # Do not allocate students with pref score less than cutoff

import math
import csv
import random
import logging
import argparse
import os
from typing import Dict, List

from utils.custom_logger import configure_logging


configure_logging()

logger = logging.getLogger(__name__)

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
    
def allocate_students(total_students, center_capacities):
    allocated_students = {}
    remaining_students = total_students

    for center in sorted(center_capacities, key=lambda x: center_capacities[x], reverse=True):
        if remaining_students > 0:
            allocation = min(center_capacities[center], remaining_students)
            allocated_students[center] = allocation
            remaining_students -= allocation
        else:
            break

    if remaining_students > 0:
        for center in sorted(center_capacities, key=lambda x: center_capacities[x], reverse=True):
            if remaining_students == 0:
                break
            if (allocated_students[center] + remaining_students) <= center_capacities[center]:
                allocated_students[center] += remaining_students
                remaining_students = 0

    return allocated_students

# Argument parser setup
parser = argparse.ArgumentParser(
    prog='center randomizer',
    description='Assigns exam centers to students based on proximity and preferences')
parser.add_argument('schools_tsv', help="Tab separated (TSV) file containing school details")
parser.add_argument('centers_tsv', help="Tab separated (TSV) file containing center details")
parser.add_argument('prefs_tsv', help="Tab separated (TSV) file containing preference scores")
parser.add_argument('-o', '--output', default='school-center.tsv', help='Output file')
args = parser.parse_args()

# Functions to read data (definitions needed)
def read_tsv(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return [dict(row) for row in csv.DictReader(file, delimiter='\t')]

def school_sort_key(school):
    return int(school['count'])  # Example sort key

# Data loading
schools = sorted(read_tsv(args.schools_tsv), key=school_sort_key)
centers = read_tsv(args.centers_tsv)
centers_remaining_cap = {c['cscode']: int(c['capacity']) for c in centers}
prefs = read_prefs(args.prefs_tsv)  # This function also needs to be defined

OUTPUT_DIR = 'results/'
create_dir(OUTPUT_DIR)  # Function to create directory

# File writing setup
with open(f"{OUTPUT_DIR}school-center-distance.tsv", 'w', encoding='utf-8') as intermediate_file, \
     open(OUTPUT_DIR + args.output, 'w', encoding='utf-8') as a_file:
    writer = csv.writer(intermediate_file, delimiter="\t")
    writer.writerow(["scode", "s_count", "school_name", "school_lat", "school_long", "cscode", "center_name", "center_address", "center_capacity", "distance_km"])
    
    allocation_file = csv.writer(a_file, delimiter='\t')
    allocation_file.writerow(["scode", "school", "cscode", "center", "center_address", "allocation", "distance_km"])

    remaining = 0  # stores count of non allocated students
    allocations = {}  # to track mutual allocations

    # Main processing loop
    for s in schools:
        centers_for_school = centers_within_distance(s, centers, PREF_DISTANCE_THRESHOLD)
        to_allot = int(s['count'])
        center_capacities = {c['cscode']: centers_remaining_cap[c['cscode']] for c in centers_for_school if c['cscode'] in centers_remaining_cap}
        
        # Allocate students using the new dynamic method
        allocations_result = allocate_students(to_allot, center_capacities)

        # Apply the allocations and update remaining capacities
        for cscode, count in allocations_result.items():
            if count > 0:
                allocate(s['scode'], cscode, count)
                centers_remaining_cap[cscode] -= count
                to_allot -= count

        # Write allocation results to files
        for cscode, count in allocations_result.items():
            c = next((center for center in centers_for_school if center['cscode'] == cscode), None)
            if c and count > 0:
                distance = haversine_distance(float(s['lat']), float(s['long']), float(c['lat']), float(c['long']))
                writer.writerow([s['scode'], s['count'], s['name-address'], s['lat'], s['long'], cscode, c['name'], c['address'], c['capacity'], distance])
                allocation_file.writerow([s['scode'], s['name-address'], cscode, c['name'], c['address'], count, distance])

        if to_allot > 0:
            remaining += to_allot
            logger.warn(f"{to_allot}/{s['count']} left for {s['scode']} {s['name-address']} centers: {len(centers_for_school)}")

    logger.info("Remaining capacity at each center (remaining_capacity cscode):")
    logger.info(sorted([(v, k) for k, v in centers_remaining_cap.items() if v != 0]))
    logger.info(f"Total remaining capacity across all centers: {sum({k: v for k, v in centers_remaining_cap.items() if v != 0}.values())}")
    logger.info(f"Students not assigned: {remaining}")
