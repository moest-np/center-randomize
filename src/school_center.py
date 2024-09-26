import math
import csv
import random
import argparse
from typing import Dict, List, Tuple

# Constants
PREF_DISTANCE_THRESHOLD = 2  # Preferred threshold distance in kilometers
ABS_DISTANCE_THRESHOLD = 7  # Absolute threshold distance in kilometers
MIN_STUDENT_IN_CENTER = 10  # Minimum number of students from a school to be assigned to a center
STRETCH_CAPACITY_FACTOR = 0.02  # How much can center capacity be stretched if need arises
PREF_CUTOFF = -4  # Do not allocate students with pref score less than cutoff

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """ Calculate the great circle distance between two points on the earth in kilometers. """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    radius_earth = 6371
    return radius_earth * c

def read_tsv(file_path: str) -> List[Dict[str, str]]:
    """ Read a TSV file and return a list of dictionaries for each row. """
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            return [row for row in reader]
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def read_prefs(file_path: str) -> Dict[str, Dict[str, int]]:
    """ Read preference scores from a TSV file into a nested dictionary. """
    prefs = {}
    data = read_tsv(file_path)
    for row in data:
        scode, cscode, pref = row['scode'], row['cscode'], int(row['pref'])
        if scode in prefs:
            prefs[scode][cscode] = prefs[scode].get(cscode, 0) + pref
        else:
            prefs[scode] = {cscode: pref}
    return prefs

def filter_and_sort_centers(school: Dict[str, str], centers: List[Dict[str, str]], distance_threshold: float, prefs: Dict[str, Dict[str, int]]) -> List[Dict[str, any]]:
    """ Filter and sort centers based on distance and preferences. """
    school_lat, school_long = float(school['lat']), float(school['long'])
    valid_centers = []
    for center in centers:
        if center['cscode'] == school['scode']:
            continue
        center_lat, center_long = float(center['lat']), float(center['long'])
        distance = haversine_distance(school_lat, school_long, center_lat, center_long)
        pref_score = prefs.get(school['scode'], {}).get(center['cscode'], 0)
        if distance <= distance_threshold and pref_score > PREF_CUTOFF:
            valid_centers.append({**center, 'distance_km': distance, 'pref_score': pref_score})

    return sorted(valid_centers, key=lambda c: (c['distance_km'], -c['pref_score']))

def allocate_centers(schools: List[Dict[str, str]], centers: List[Dict[str, str]], prefs: Dict[str, Dict[str, int]]) -> Tuple[Dict[str, Dict[str, int]], int]:
    """ Allocate centers to schools based on preferences and capacities. """
    allocations = {}
    remaining_students = 0
    centers_capacity = {c['cscode']: int(c['capacity']) for c in centers}

    for school in schools:
        needed = int(school['count'])
        centers_for_school = filter_and_sort_centers(school, centers, PREF_DISTANCE_THRESHOLD, prefs)
        for center in centers_for_school:
            if needed <= 0:
                break
            allot = min(needed, centers_capacity[center['cscode']], MIN_STUDENT_IN_CENTER)
            if centers_capacity[center['cscode']] >= allot:
                if school['scode'] not in allocations:
                    allocations[school['scode']] = {}
                allocations[school['scode']][center['cscode']] = allocations[school['scode']].get(center['cscode'], 0) + allot
                centers_capacity[center['cscode']] -= allot
                needed -= allot

        if needed > 0:  # If students are still unallocated, attempt with a relaxed distance threshold
            expanded_centers = filter_and_sort_centers(school, centers, ABS_DISTANCE_THRESHOLD, prefs)
            for center in expanded_centers:
                if needed <= 0:
                    break
                stretched_capacity = math.floor(int(center['capacity']) * STRETCH_CAPACITY_FACTOR + centers_capacity[center['cscode']])
                allot = min(needed, max(stretched_capacity, MIN_STUDENT_IN_CENTER))
                if stretched_capacity >= allot:
                    if school['scode'] not in allocations:
                        allocations[school['scode']] = {}
                    allocations[school['scode']][center['cscode']] = allocations[school['scode']].get(center['cscode'], 0) + allot
                    centers_capacity[center['cscode']] -= allot
                    needed -= allot

        remaining_students += needed

    return allocations, remaining_students

def main():
    parser = argparse.ArgumentParser(description='Assigns exam centers to students based on preferences.')
    parser.add_argument('schools_tsv', help="Tab separated file containing school details")
    parser.add_argument('centers_tsv', help="Tab separated file containing center details")
    parser.add_argument('prefs_tsv', help="Tab separated file containing preference scores")
    parser.add_argument('-o', '--output', default='school-center.tsv', help='Output file')
    args = parser.parse_args()

    schools = read_tsv(args.schools_tsv)
    centers = read_tsv(args.centers_tsv)
    prefs = read_prefs(args.prefs_tsv)

    allocations, remaining_students = allocate_centers(schools, centers, prefs)

    # Output results
    with open(args.output, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow(["scode", "school", "cscode", "center", "center_address", "allocation", "distance_km"])
        for scode, school_allocations in allocations.items():
            for cscode, count in school_allocations.items():
                school = next((s for s in schools if s['scode'] == scode), None)
                center = next((c for c in centers if c['cscode'] == cscode), None)
                if school and center:
                    print(school)
                    writer.writerow([scode, school['name-address'], cscode, center['name'], center['address'], count, center.get('distance_km', '')])

    print(f"Total students not assigned: {remaining_students}")

if __name__ == '__main__':
    main()
