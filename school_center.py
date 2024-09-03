from utils.custom_logger import configure_logging
from typing import Dict, List
from os import sys, path, makedirs
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
DEFAULT_OUTPUT_DIR = 'results'  # Default directory to create output files if --output not provided
DEFAULT_OUTPUT_FILENAME = 'school-center.tsv'

configure_logging()
logger = logging.getLogger(__name__)



def haversine_distance(lat1, lon1, lat2, lon2):
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
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    radius_earth = 6371    # Average Radius of Earth in km
    distance = radius_earth * c
    return distance


def centers_within_distance(school: Dict[str, str], centers: Dict[str, str], distance_threshold: float, relax_threshold: bool) -> List[Dict[str, any]]:
    """
    Return List of centers that are within given distance from school.
    relax_threshold: If there are no centers within given distance return one that is closest
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
        return c['distance_km'] * random.uniform(1, 5) - get_pref(school['scode'], c['cscode']) * 100
    
    school_lat = school.get('lat')
    school_long = school.get('long')
    if len(school_lat) == 0 or len(school_long) == 0:
        return []

    qualifying_centers = []
    # nearest_distance = None
    # nearest_center = None
    for c in centers:
        if school['scode'] == c['cscode'] \
            or is_allocated(c['cscode'], s['scode']) \
            or get_pref(school['scode'], c['cscode']) <= PREF_CUTOFF:
            continue
        distance = haversine_distance(float(school_lat), float(
            school_long), float(c.get('lat')), float(c.get('long')))
        # if nearest_center is None or distance < nearest_distance:
        #     nearest_center = c
        #     nearest_distance = distance
        qualifying_centers.append(center_to_dict(c, distance))

    within_distance = [ c for c in qualifying_centers if c['distance_km'] <= distance_threshold ]
    if len(within_distance) > 0:
        return sorted(within_distance, key=sort_key) 
    elif relax_threshold: # if there are no centers within given threshold, return one that is closest
        return sorted(qualifying_centers, key=sort_key) 
    else: 
        return []

def read_tsv(file_path: str) -> List[Dict[str, str]]:
    """
    Function to read the tsv file for school.tsv and centers.tsv
    Return a list of schools/centers as dicts.
    """
    data = []
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                data.append(dict(row))
    except FileNotFoundError as e:
        logger.error(f"File '{file_path} : {e}' not found.")
        sys.exit(1)
    except PermissionError as e:
        logger.error(f"Permission denied while accessing file '{file_path}' : {e}.")
        sys.exit(1)
    except IOError as e:
        logger.error(f"Error opening or reading file: '{file_path}' : {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred while reading file '{file_path}' : {e}")
        sys.exit(1)
    return data


def read_prefs(file_path: str) -> Dict[str, Dict[str, int]]:
    """
    Read the tsv file for pref.tsv
    Return a dict of dicts key scode and then cscode
    """
    prefs = {}
    try:
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
    except FileNotFoundError as e:
        logger.error(f"File '{file_path} :{e}' not found.")
        sys.exit(1)
    except PermissionError as e:
        logger.error(f"Permission denied while accessing file '{file_path}:{e}'.")
        sys.exit(1)
    except IOError as e:
        logger.error(f"Error opening or reading file: {file_path} :{e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred while reading file '{file_path}': {e}")
        sys.exit(1)
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

def validate_data(schools, centers, prefs):
    # Ensure all necessary fields are present and valid
    for school in schools:
        if not all(k in school for k in ('scode', 'name-address', 'lat', 'long', 'count')):
            logger.error(f"Invalid school data: {school}")
            sys.exit(1)
    for center in centers:
        if not all(k in center for k in ('cscode', 'name', 'address', 'lat', 'long', 'capacity')):
            logger.error(f"Invalid center data: {center}")
            sys.exit(1)
    # Validate preference scores similarly
    for scode, center_prefs in prefs.items():
        for cscode, pref in center_prefs.items():
            if not isinstance(pref, int):
                logger.error(f"Invalid preference data: scode={scode}, cscode={cscode}, pref={pref}")
                sys.exit(1)

parser = argparse.ArgumentParser(
    prog='center randomizer',
    description='Assigns centers to exam centers to students')
parser.add_argument('schools_tsv', default='schools.tsv',
                    help="Tab separated (TSV) file containing school details")
parser.add_argument('centers_tsv', default='centers.tsv',
                    help="Tab separated (TSV) file containing center details")
parser.add_argument('prefs_tsv', default='prefs.tsv',
                    help="Tab separated (TSV) file containing preference scores")
parser.add_argument('-o', '--output', default = DEFAULT_OUTPUT_FILENAME, 
                    help='Output file')
parser.add_argument('-s', '--seed', action='store', metavar='SEEDVALUE',
                     default=None, type=float, 
                     help='Initialization seed for Random Number Generator')

args = parser.parse_args()

random = random.Random(args.seed) #overwrites the random module to use seeded rng

schools = sorted(read_tsv(args.schools_tsv), key= school_sort_key)
centers = read_tsv(args.centers_tsv)
centers_remaining_cap = {c['cscode']: int(c['capacity']) for c in centers}
prefs = read_prefs(args.prefs_tsv)

validate_data(schools, centers, prefs) #Validate Data Here

remaining = 0       # stores count of non allocated students
allocations = {}    # to track mutual allocations

def get_output_dir():
    dirname = path.dirname(args.output)
    if(dirname):
        return dirname
    else:
        return DEFAULT_OUTPUT_DIR

def get_output_filename():
    basename = path.basename(args.output)
    if(basename):
        return basename
    else:
        return DEFAULT_OUTPUT_FILENAME


output_dirname = get_output_dir()
output_filename = get_output_filename()
makedirs(output_dirname, exist_ok=True) # Create the output directory if not exists

with open(path.join(output_dirname, "school-center-distance.tsv"), 'w', encoding='utf-8') as intermediate_file, \
open(path.join(output_dirname, output_filename), 'w', encoding='utf-8') as a_file:
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
                              "center_lat",
                              "center_long",
                              "allocation", 
                              "distance_km"])

    for s in schools:
        centers_for_school = centers_within_distance(
            s, centers, PREF_DISTANCE_THRESHOLD, False)
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
                s, centers, ABS_DISTANCE_THRESHOLD, True)
            for c in expanded_centers:
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
                                      c['lat'],
                                      c['long'],
                                      allocations[s['scode']][c['cscode']], 
                                      c['distance_km']])

        if to_allot > 0:
            remaining += to_allot
            logger.warning(
                f"{to_allot}/{s['count']} left for {s['scode']} {s['name-address']} centers: {len(centers_for_school)}")

    logger.info("Remaining capacity at each center (remaining_capacity cscode):")
    logger.info(sorted([(v, k)
                for k, v in centers_remaining_cap.items() if v != 0]))
    logger.info(
        f"Total remaining capacity across all centers: {sum({k:v for k, v in centers_remaining_cap.items() if v != 0}.values())}")
    logger.info(f"Students not assigned: {remaining}")