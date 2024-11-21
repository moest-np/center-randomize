from utils.custom_logger import configure_logging
from typing import Dict, List
import os
import argparse
import logging
import random
import csv
import math

# Parameters
PREF_DISTANCE_THRESHOLD = 2     # Preferred threshold distance in km
ABS_DISTANCE_THRESHOLD = 7      # Absolute threshold distance in km
MIN_STUDENT_IN_CENTER = 10      # Min. no of students from a school to be assigned to a center in normal circumstances
STRETCH_CAPACITY_FACTOR = 0.02  # How much can center capacity be streched if need arises
PREF_CUTOFF = -4                # Do not allocate students with pref score less than cutoff

configure_logging()
logger = logging.getLogger(__name__)


def create_dir(dirPath: str):
    """
    Create the given directory if it doesn't exists
    - Creates all the directories needed to resolve to the provided directory path
    """
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)


def get_distance(scode: str, cscode: str) -> float:
    """
    Returns the route distance calculated previously
    """
    with open("./results/distance.tsv", 'r', encoding='utf-8') as file:
        next(file)  # Skip header row
        for line in file:
            fields = line.strip().split('\t')
            if len(fields) >= 2:  # Ensure at least two columns exist
                if fields[0] == scode and fields[2] == cscode:
                    # Match found, return the row
                    return float(fields[4])
    # If no match found, return None or handle as needed
    return None


def centers_within_distance(school: Dict[str, str], centers: Dict[str, str], distance_threshold: float) -> List[Dict[str, any]]:
    """
    Return List of centers that are within given distance from school.
    If there are no centers within given distance return one that is closest
    Returned params :
            {'cscode', 'name', 'address', 'capacity', 'lat', 'long', 'distance_km'}

    """
    def center_to_dict(c, distance):
        return {'cscode': c['cscode'], 
                 'name': c['name'], 
                 'address': c['address'], 
                 'capacity': c['capacity'], 
                 'lat': c['lat'], 
                 'long': c['long'], 
                 'distance_km': distance}

    def sort_key(c):
        # intent: sort by preference score DESC then by distance_km ASC
        # leaky abstraction - sorted requires a single numeric value for each element
        return c['distance_km'] * random.uniform(1, 5) - get_pref(school['scode'], c['cscode'])*100

    school_lat = school.get('lat')
    school_long = school.get('long')
    if len(school_lat) == 0 or len(school_long) == 0:
        return []

    within_distance = []
    nearest_distance = None
    nearest_center = None
    for c in centers:
        distance = get_distance(school.get('scode'),c.get('cscode'))
        if school['scode'] == c['cscode']:
            continue
        if nearest_center == None or distance < nearest_distance:
            nearest_center = c
            nearest_distance = distance

        if distance <= distance_threshold and get_pref(school['scode'], c['cscode']) > PREF_CUTOFF:
            within_distance.append(center_to_dict(c, distance))

    if len(within_distance) > 0:
        return sorted(within_distance, key=sort_key)
    else:  # if there are no centers within given  threshold, return one that is closest
        return [center_to_dict(nearest_center, nearest_distance)]


def read_tsv(file_path: str) -> List[Dict[str, str]]:
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


def read_prefs(file_path: str) -> Dict[str, Dict[str, int]]:
    """
    Read the tsv file for pref.tsv
    Return a dict of dicts key scode and then cscode
    """
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
    """
    Return the preference score for the given school and center.
    If the school has no preference for the center return 0.
    """
    if prefs.get(scode):
        if prefs[scode].get(cscode):
            return prefs[scode][cscode]
        else:
            return 0
    else:
        return 0


def calc_per_center(count: int) -> int:
    """
    Return the number of students that can be allocated to a center based on student count.
    """
    if count <= 400:
        return 100
    # elif count <= 900:
    #     return 200
    else: 
        return 200


def school_sort_key(s):
    # intent: allocate students from schools with large students count first
    # to avoid excessive fragmentation
    return (-1 if int(s['count']) > 500 else 1) * random.uniform(1, 100)


def allocate(scode: str, cscode: str, count: int):
    """
    Allocate the given number of students to the given center.
    """
    if scode not in allocations:
        allocations[scode] = {cscode: count}
    elif cscode not in allocations[scode]:
        allocations[scode][cscode] = count
    else:
        allocations[scode][cscode] += count


def is_allocated(scode1: str, scode2: str) -> bool:
    """
    Return true if the given school has been allocated to the given center.
    """
    return allocations.get(scode1, {}).get(scode2) is not None


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
parser.add_argument('-s', '--seed', action='store', metavar='SEEDVALUE',
                     default=None, type=float, 
                     help='Initialization seed for Random Number Generator')

args = parser.parse_args()

random = random.Random(args.seed) #overwrites the random module to use seeded rng

schools = sorted(read_tsv(args.schools_tsv), key= school_sort_key)
centers = read_tsv(args.centers_tsv)
centers_remaining_cap = {c['cscode']: int(c['capacity']) for c in centers}
prefs = read_prefs(args.prefs_tsv)

remaining = 0       # stores count of non allocated students
allocations = {}    # to track mutual allocations

OUTPUT_DIR = 'results/'
create_dir(OUTPUT_DIR)  # Create the output directory if not exists
with open('{}school-center-distance.tsv'.format(OUTPUT_DIR), 'w', encoding='utf-8') as intermediate_file, \
        open(OUTPUT_DIR + args.output, 'w', encoding='utf-8') as a_file:
    writer = csv.writer(intermediate_file, delimiter="\t")
    writer.writerow(["scode", 
                     "s_count", 
                     "school_name", 
                     "school_lat", 
                     "school_long",
                     "cscode", 
                     "center_name", 
                     "center_address", 
                     "center_capacity", 
                     "distance_km"])

    allocation_file = csv.writer(a_file, delimiter='\t')
    allocation_file.writerow(["scode", 
                              "school", 
                              "cscode", 
                              "center", 
                              "center_address", 
                              "allocation", 
                              "distance_km"])

    for s in schools:
        centers_for_school = centers_within_distance(
            s, centers, PREF_DISTANCE_THRESHOLD)
        to_allot = int(s['count'])
        per_center = calc_per_center(to_allot)

        allocated_centers = {}

        # per_center = math.ceil(to_allot / min(calc_num_centers(to_allot), len(centers_for_school)))
        for c in centers_for_school:
            writer.writerow([s['scode'], 
                             s['count'], 
                             s['name-address'], 
                             s['lat'], 
                             s['long'],
                             c['cscode'], 
                             c['name'], 
                             c['address'], 
                             c['capacity'], 
                             c['distance_km']])
            if is_allocated(c['cscode'], s['scode']):
                continue
            next_allot = min(to_allot, per_center, max(
                centers_remaining_cap[c['cscode']], MIN_STUDENT_IN_CENTER))
            if to_allot > 0 and next_allot > 0 and centers_remaining_cap[c['cscode']] >= next_allot:
                allocated_centers[c['cscode']] = c
                allocate(s['scode'], c['cscode'], next_allot)
                # allocation.writerow([s['scode'], s['name-address'], c['cscode'], c['name'], c['address'], next_allot, c['distance_km']])
                to_allot -= next_allot
                centers_remaining_cap[c['cscode']] -= next_allot

        if to_allot > 0:  # try again with relaxed constraints and more capacity at centers
            expanded_centers = centers_within_distance(
                s, centers, ABS_DISTANCE_THRESHOLD)
            for c in expanded_centers:
                if is_allocated(c['cscode'], s['scode']):
                    continue
                stretched_capacity = math.floor(
                    int(c['capacity']) * STRETCH_CAPACITY_FACTOR + centers_remaining_cap[c['cscode']])
                next_allot = min(to_allot, max(
                    stretched_capacity, MIN_STUDENT_IN_CENTER))
                if to_allot > 0 and next_allot > 0 and stretched_capacity >= next_allot:
                    allocated_centers[c['cscode']] = c
                    allocate(s['scode'], c['cscode'], next_allot)
                    # allocation.writerow([s['scode'], s['name-address'], c['cscode'], c['name'], c['address'], next_allot, c['distance_km']])
                    to_allot -= next_allot
                    centers_remaining_cap[c['cscode']] -= next_allot

        for c in allocated_centers.values():
            allocation_file.writerow([s['scode'], 
                                      s['name-address'], 
                                      c['cscode'], 
                                      c['name'],
                                      c['address'], 
                                      allocations[s['scode']][c['cscode']], 
                                      c['distance_km']])

        if to_allot > 0:
            remaining += to_allot
            logger.warn(
                f"{to_allot}/{s['count']} left for {s['scode']} {s['name-address']} centers: {len(centers_for_school)}")

    logger.info("Remaining capacity at each center (remaining_capacity cscode):")
    logger.info(sorted([(v, k)
                for k, v in centers_remaining_cap.items() if v != 0]))
    logger.info(
        f"Total remaining capacity across all centers: {sum({k:v for k, v in centers_remaining_cap.items() if v != 0}.values())}")
    logger.info(f"Students not assigned: {remaining}")
