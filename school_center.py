from utils.custom_logger import configure_logging
from utils.allocation import merge_small_allocations
from collections import namedtuple
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
MAX_ATTEMPTS = 10               # Max. no of times to run the allocation if students are left without a center
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
            or is_allocated(c['cscode'], school['scode']) \
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
parser.add_argument('-a', '--max-attempts', type=int, default=MAX_ATTEMPTS,
                    help='Number of times to run the allocation if students are left without a center, '
                         'the best run is kept')

args = parser.parse_args()
if args.max_attempts < 1:
    parser.error('--max-attempts must be at least 1')

random = random.Random(args.seed) #overwrites the random module to use seeded rng

all_schools = read_tsv(args.schools_tsv)
centers = read_tsv(args.centers_tsv)
center_capacity = {c['cscode']: int(c['capacity']) for c in centers}
prefs = read_prefs(args.prefs_tsv)

centers_remaining_cap = {}  # remaining capacity of each center, reset for every attempt
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

class RowBuffer:
    """
    Collects the rows of one attempt, only the rows of the best attempt are written to file.
    """
    def __init__(self):
        self.rows = []

    def writerow(self, row):
        self.rows.append(row)


Attempt = namedtuple('Attempt', ['distance_rows', 'allocation_rows', 'remaining', 'remaining_cap',
                                 'left_messages'])


def run_allocation() -> Attempt:
    """
    Allocate the students of all schools to centers, schools in a random order.
    Return the rows for the output files and the number of students left without a center.
    """
    global centers_remaining_cap, remaining, allocations
    centers_remaining_cap = dict(center_capacity)
    remaining = 0
    allocations = {}
    left_messages = []   # warnings about schools with students left, logged for the kept attempt
    schools = sorted(all_schools, key=school_sort_key)

    writer = RowBuffer()
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

    allocation_file = RowBuffer()
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

        # Avoid a small number of students at a center, e.g. 100 + 100 + 7 becomes 107 + 100
        if allocated_centers:
            school_allocation = allocations[s['scode']]
            # Only the centers of this row, a duplicate scode in schools.tsv would add more
            this_allocation = {cscode: school_allocation[cscode] for cscode in allocated_centers}
            spare = {cscode: math.floor(
                        center_capacity[cscode] * STRETCH_CAPACITY_FACTOR + centers_remaining_cap[cscode])
                     for cscode in this_allocation}
            moves = merge_small_allocations(this_allocation, spare, MIN_STUDENT_IN_CENTER)
            for small, target in moves.items():
                moved = school_allocation.pop(small)
                school_allocation[target] += moved
                centers_remaining_cap[small] += moved
                centers_remaining_cap[target] -= moved
                del allocated_centers[small]

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
            left_messages.append(
                f"{to_allot}/{s['count']} left for {s['scode']} {s['name-address']} centers: {len(centers_for_school)}")

    return Attempt(writer.rows, allocation_file.rows, remaining, centers_remaining_cap, left_messages)


def unplaceable_students() -> int:
    """
    Students of schools that no attempt can give a center: no coordinates, or every
    center is the school itself or excluded by the preferences.
    """
    total = 0
    for s in all_schools:
        has_center = any(c['cscode'] != s['scode'] and get_pref(s['scode'], c['cscode']) > PREF_CUTOFF
                         for c in centers)
        if not (s.get('lat') and s.get('long')) or not has_center:
            total += int(s['count'])
    return total


# Empty the output files, as when they were opened before the allocation, so that
# results of an earlier run are never mistaken for this one if the program fails
for filename in ("school-center-distance.tsv", output_filename):
    open(path.join(output_dirname, filename), 'w', encoding='utf-8').close()

# Run again, with schools in a new random order, while students are left without a center
best = None
best_attempt = 0
fewest_possible = None   # students that no attempt can place, only worked out if needed
for attempt in range(1, args.max_attempts + 1):
    result = run_allocation()
    if best is None or result.remaining < best.remaining:
        best, best_attempt = result, attempt
    if result.remaining == 0:
        break
    if fewest_possible is None:
        fewest_possible = unplaceable_students()
    if best.remaining <= fewest_possible:
        break   # another attempt can not do better
    logger.warning(
        f"Attempt {attempt}/{args.max_attempts}: {result.remaining} students not assigned"
        + (", trying again" if attempt < args.max_attempts else ""))

if best.remaining > 0:
    for message in best.left_messages:
        logger.warning(message)
    logger.error(
        f"{best.remaining} students are still not assigned to a center after {attempt} "
        f"attempt{'s' if attempt > 1 else ''}. Check the schools above, more centers or "
        "more capacity may be needed")
if attempt > 1:
    logger.info(f"Result of attempt {best_attempt} of {attempt} kept")

with open(path.join(output_dirname, "school-center-distance.tsv"), 'w', encoding='utf-8') as intermediate_file, \
open(path.join(output_dirname, output_filename), 'w', encoding='utf-8') as a_file:
    csv.writer(intermediate_file, delimiter="\t").writerows(best.distance_rows)
    csv.writer(a_file, delimiter='\t').writerows(best.allocation_rows)

logger.info("Remaining capacity at each center (remaining_capacity cscode):")
logger.info(sorted([(v, k)
            for k, v in best.remaining_cap.items() if v != 0]))
logger.info(
    f"Total remaining capacity across all centers: {sum({k:v for k, v in best.remaining_cap.items() if v != 0}.values())}")
logger.info(f"Students not assigned: {best.remaining}")
