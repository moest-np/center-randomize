# Constants for distance thresholds, minimum student count, and capacity factors
from utils.custom_logger import configure_logging
from typing import Dict, List
import os
import argparse
import logging
import random
import csv
import math
OUTPUT_DIR = 'results/'
PREF_DISTANCE_THRESHOLD = 2  # Preferred distance threshold in kilometers
ABS_DISTANCE_THRESHOLD = 7  # Absolute distance threshold in kilometers
# Minimum number of students from a school to be assigned to a center in normal circumstances
MIN_STUDENT_IN_CENTER = 10
STRETCH_CAPACITY_FACTOR = 0.02  # Capacity stretching factor
PREF_CUTOFF = -4  # Preference score cutoff


# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

# Function to create directory if it doesn't exist


def create_directory(dir_path: str):
    """
    Create the given directory if it doesn't exist.
    Creates all the directories needed to resolve to the provided directory path.
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

# Function to calculate haversine distance between two points


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth specified in decimal degrees.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * \
        math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    radius_earth = 6371  # Radius of Earth in kilometers
    distance = radius_earth * c
    return distance

# Function to find centers within a certain distance from a school


def find_centers_within_distance(school: Dict[str, str], centers: Dict[str, str], distance_threshold: float) -> List[Dict[str, any]]:
    """
    Return a list of centers that are within a given distance from a school.
    If there are no centers within the given distance, return the nearest one.
    Returned parameters:
            {'cscode', 'name', 'address', 'capacity', 'lat', 'long', 'distance_km'}
    """
    def center_to_dict(c, distance):
        return {'cscode': c['cscode'], 'name': c['name'], 'address': c['address'], 'capacity': c['capacity'], 'lat': c['lat'], 'long': c['long'], 'distance_km': distance}

    def sort_key(c):
        # Sort by preference score descending, then by distance_km ascending
        return c['distance_km'] * random.uniform(1, 5) - get_preference_score(school['scode'], c['cscode']) * 100

    school_lat = school.get('lat')
    school_long = school.get('long')
    if len(school_lat) == 0 or len(school_long) == 0:
        return []

    within_distance = []
    nearest_distance = None
    nearest_center = None
    for c in centers:
        distance = haversine_distance(float(school_lat), float(
            school_long), float(c.get('lat')), float(c.get('long')))
        if school['scode'] == c['cscode']:
            continue
        if nearest_center == None or distance < nearest_distance:
            nearest_center = c
            nearest_distance = distance

        if distance <= distance_threshold and get_preference_score(school['scode'], c['cscode']) > PREF_CUTOFF:
            within_distance.append(center_to_dict(c, distance))

    if len(within_distance) > 0:
        return sorted(within_distance, key=sort_key)
    else:  # If there are no centers within the given threshold, return the nearest one
        return [center_to_dict(nearest_center, nearest_distance)]

# Function to read data from a TSV file


def read_tsv(file_path: str) -> List[Dict[str, str]]:
    data = []
    with open(file_path, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            data.append(dict(row))
    return data

# Function to read preference scores from a TSV file


def read_preference_scores(file_path: str) -> Dict[str, Dict[str, int]]:
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

# Function to get preference score


def get_preference_score(scode, cscode) -> int:
    if prefs.get(scode):
        if prefs[scode].get(cscode):
            return prefs[scode][cscode]
        else:
            return 0
    else:
        return 0

# Function to calculate per center count


def calculate_per_center(count: int) -> int:
    if count <= 400:
        return 100
    else:
        return 200

# Function to sort schools


def school_sort_key(s):
    return (-1 if int(s['count']) > 500 else 1) * random.uniform(1, 100)

# Function to allocate students to centers


def allocate_students(scode: str, cscode: str, count: int):
    if allocations.get(scode) == None:
        allocations[scode] = {cscode: count}
    elif allocations[scode].get(cscode) == None:
        allocations[scode][cscode] = count
    else:
        allocations[scode][cscode] += count

# Function to check if a school is allocated to a center


def is_allocated_to_center(scode1: str, scode2: str) -> bool:
    if allocations.get(scode1):
        return allocations[scode1].get(scode2) != None
    else:
        return False


# Argument parser for command line interface
parser = argparse.ArgumentParser(
    prog='center randomizer',
    description='Assigns centers to exam centers to students')
parser.add_argument('schools_tsv', default='schools.tsv',
                    help="Tab separated (TSV) file containing school details")
parser.add_argument('centers_tsv', default='centers.tsv',
                    help="Tab separated (TSV) file containing center details")
parser.add_argument('prefs_tsv', default='prefs.tsv',
                    help="Tab separated (TSV) file containing preference scores")
parser.add_argument(
    '-o', '--output', default='school-center.tsv', help='Output file')
parser.add_argument('-s', '--seed', action='store', metavar='SEEDVALUE', default=None,
                    type=float, help='Initialization seed for Random Number Generator')

args = parser.parse_args()

random.seed(args.seed)  # Seed the random number generator

# Read data from TSV files
schools = sorted(read_tsv(args.schools_tsv), key=school_sort_key)
centers = read_tsv(args.centers_tsv)
centers_remaining_capacity = {c['cscode']: int(c['capacity']) for c in centers}
prefs = read_preference_scores(args.prefs_tsv)

remaining_students = 0  # Count of non-allocated students
allocations = {}  # Dictionary to track allocations

create_directory(OUTPUT_DIR)  # Create the output directory if it doesn't exist

# Open output files
with open('{}school-center-distance.tsv'.format(OUTPUT_DIR), 'w', encoding='utf-8') as intermediate_file, \
        open(OUTPUT_DIR + args.output, 'w', encoding='utf-8') as allocation_file:
    writer = csv.writer(intermediate_file, delimiter="\t")
    writer.writerow(["scode", "s_count", "school_name", "school_lat", "school_long",
                    "cscode", "center_name", "center_address", "center_capacity", "distance_km"])

    allocation_writer = csv.writer(allocation_file, delimiter='\t')
    allocation_writer.writerow(
        ["scode", "school", "cscode", "center", "center_address", "allocation", "distance_km"])

    for school in schools:
        centers_for_school = find_centers_within_distance(
            school, centers, PREF_DISTANCE_THRESHOLD)
        to_allocate = int(school['count'])
        per_center_count = calculate_per_center(to_allocate)

        allocated_centers = {}

        for center in centers_for_school:
            writer.writerow([school['scode'], school['count'], school['name-address'], school['lat'], school['long'],
                            center['cscode'], center['name'], center['address'], center['capacity'], center['distance_km']])
            if is_allocated_to_center(center['cscode'], school['scode']):
                continue
            next_allocation = min(to_allocate, per_center_count, max(
                centers_remaining_capacity[center['cscode']], MIN_STUDENT_IN_CENTER))
            if to_allocate > 0 and next_allocation > 0 and centers_remaining_capacity[center['cscode']] >= next_allocation:
                allocated_centers[center['cscode']] = center
                allocate_students(
                    school['scode'], center['cscode'], next_allocation)
                to_allocate -= next_allocation
                centers_remaining_capacity[center['cscode']] -= next_allocation

        if to_allocate > 0:  # Try again with relaxed constraints and more capacity at centers
            expanded_centers = find_centers_within_distance(
                school, centers, ABS_DISTANCE_THRESHOLD)
            for center in expanded_centers:
                if is_allocated_to_center(center['cscode'], school['scode']):
                    continue
                stretched_capacity = math.floor(int(
                    center['capacity']) * STRETCH_CAPACITY_FACTOR + centers_remaining_capacity[center['cscode']])
                next_allocation = min(to_allocate, max(
                    stretched_capacity, MIN_STUDENT_IN_CENTER))
                if to_allocate > 0 and next_allocation > 0 and stretched_capacity >= next_allocation:
                    allocated_centers[center['cscode']] = center
                    allocate_students(
                        school['scode'], center['cscode'], next_allocation)
                    to_allocate -= next_allocation
                    centers_remaining_capacity[center['cscode']
                                               ] -= next_allocation

        for center in allocated_centers.values():
            allocation_writer.writerow([school['scode'], school['name-address'], center['cscode'], center['name'],
                                       center['address'], allocations[school['scode']][center['cscode']], center['distance_km']])

        if to_allocate > 0:
            remaining_students += to_allocate
            logger.warning(f"{to_allocate}/{school['count']} students left for {
                           school['scode']} {school['name-address']} centers: {len(centers_for_school)}")

    logger.info("Remaining capacity at each center (remaining_capacity cscode):")
    logger.info(
        sorted([(v, k) for k, v in centers_remaining_capacity.items() if v != 0]))
    logger.info(f"Total remaining capacity across all centers: {
                sum({k: v for k, v in centers_remaining_capacity.items() if v != 0}.values())}")
    logger.info(f"Students not assigned: {remaining_students}")
