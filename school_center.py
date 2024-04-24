import math
import random
import logging
import argparse
from typing import Dict, List

from utils.custom_logger import configure_logging
from utils.constants import CENTER_DISTANCE_OUTPUT_FILE, EARTH_RADIUS, OUTPUT_DIR,PREF_DISTANCE_THRESHOLD,ABS_DISTANCE_THRESHOLD,MIN_STUDENT_IN_CENTER,STRETCH_CAPACITY_FACTOR,PREF_CUTOFF
from utils.file_utils import FileUtils;
class CentersAllocation:
    
    def __init__(self):
        configure_logging()
        self.logger = logging.getLogger(__name__)
        self.allocations = {}  # to track mutual allocations
        self.fileUtils = FileUtils()

    def haversine_distance(self,lat1, lon1, lat2, lon2):
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
        distance = EARTH_RADIUS * c
        return distance

    def centers_within_distance(self,school: Dict[str, str], centers: Dict[str, str], distance_threshold: float) -> List[Dict[str, any]]:
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
            return c['distance_km'] * random.uniform(1,5) - self.get_pref(school['scode'], c['cscode'])*100
        
        school_lat = school.get('lat')
        school_long = school.get('long')
        if len(school_lat) == 0 or len(school_long) == 0:
            return []
        
        within_distance = []
        nearest_distance = None
        nearest_center = None
        for c in centers: 
            distance = self.haversine_distance(float(school_lat), float(school_long), float(c.get('lat')), float(c.get('long')))
            if school['scode'] == c['cscode']:
                continue
            if nearest_center == None or distance < nearest_distance:
                nearest_center = c
                nearest_distance = distance

            if distance <= distance_threshold and self.get_pref(school['scode'], c['cscode']) > PREF_CUTOFF:
                within_distance.append(center_to_dict(c, distance))
                
        if len(within_distance) > 0:
            return sorted(within_distance, key=sort_key) 
        else: # if there are no centers within given  threshold, return one that is closest
            return [center_to_dict(nearest_center, nearest_distance)]

    def get_pref(self,scode, cscode) -> int:
        """
        Read the tsv file for pref.tsv
        Return a dict of dicts key scode and then cscode
        """
        if self.prefs.get(scode):
            if self.prefs[scode].get(cscode):
                return self.prefs[scode][cscode]
            else:
                return 0
        else:
            return 0 

    def calc_per_center(self,count: int) -> int: 
        """
        Return the number of students that can be allocated to a center based on student count.
        """
        if count <= 400:
            return 100
        # elif count <= 900:
        #     return 200
        else: 
            return 200

    def school_sort_key(self,s):
        return (-1 if int(s['count']) > 500 else 1 ) * random.uniform(1, 100)

    def allocate(self,scode:str, cscode:str, count: int):
        """
        Allocate the given number of students to the given center.
        """
        if scode not in self.allocations:
            self.allocations[scode] = {cscode: count}
        elif cscode not in self.allocations[scode]:
            self.allocations[scode][cscode] = count
        else:
            self.allocations[scode][cscode] += count

    def is_allocated(self,scode1: str, scode2:str) -> bool:
        """
        Return true if the given school has been allocated to the given center.
        """
        return self.allocations.get(scode1, {}).get(scode2) is not None

    def start_allocation(self):
        parser = argparse.ArgumentParser(prog='center randomizer',description='Assigns centers to exam centers to students')
        parser.add_argument('schools_tsv', default='schools.tsv', help="Tab separated (TSV) file containing school details")
        parser.add_argument('centers_tsv', default='centers.tsv', help="Tab separated (TSV) file containing center details")
        parser.add_argument('prefs_tsv', default='prefs.tsv', help="Tab separated (TSV) file containing preference scores")
        parser.add_argument('-o', '--output', default='school-center.tsv', help='Output file')
        parser.add_argument('-s', '--seed', action='store', metavar='SEEDVALUE', default=None, type=float, help='Initialization seed for Random Number Generator')

        args = parser.parse_args()
        global random 
        if args.seed:
            random = random.Random(args.seed) #overwrites the random module to use seeded rng

        schools = sorted(self.fileUtils.read_tsv(args.schools_tsv), key= self.school_sort_key)
        centers = self.fileUtils.read_tsv(args.centers_tsv)
        centers_remaining_cap = {c['cscode']:int(c['capacity']) for c in centers}
        self.prefs = self.fileUtils.read_prefs(args.prefs_tsv)

        remaining = 0 # stores count of non allocated students 

        self.fileUtils.create_dir(OUTPUT_DIR) # Create the output directory if not exists
        with self.fileUtils.openOutputFiles(CENTER_DISTANCE_OUTPUT_FILE,OUTPUT_DIR) as intermediate_file, \
        self.fileUtils.openOutputFiles(args.output,OUTPUT_DIR) as a_file:
            writer = self.fileUtils.get_csv_writer(intermediate_file,delimiter='\t')
            writer.writerow(["scode", "s_count", "school_name", "school_lat", "school_long", "cscode", "center_name", "center_address", "center_capacity", "distance_km"])
            
            allocation_file = self.fileUtils.get_csv_writer(a_file, delimiter='\t')
            allocation_file.writerow(["scode", "school", "cscode", "center", "center_address", "allocation", "distance_km"])
            
            for s in schools:
                centers_for_school = self.centers_within_distance(s, centers, PREF_DISTANCE_THRESHOLD)
                to_allot = int(s['count'])
                per_center = self.calc_per_center(to_allot)

                allocated_centers = {}

                # per_center = math.ceil(to_allot / min(calc_num_centers(to_allot), len(centers_for_school))) 
                for c in centers_for_school:
                    writer.writerow([s['scode'], s['count'], s['name-address'], s['lat'], s['long'], c['cscode'], c['name'], c['address'], c['capacity'], c['distance_km'] ])
                    if self.is_allocated(c['cscode'], s['scode']):
                        continue
                    next_allot = min(to_allot, per_center, max(centers_remaining_cap[c['cscode']], MIN_STUDENT_IN_CENTER))
                    if to_allot > 0 and next_allot > 0 and centers_remaining_cap[c['cscode']] >= next_allot:
                        allocated_centers[c['cscode']] = c
                        self.allocate(s['scode'], c['cscode'], next_allot)
                        # allocation.writerow([s['scode'], s['name-address'], c['cscode'], c['name'], c['address'], next_allot, c['distance_km']])
                        to_allot -= next_allot
                        centers_remaining_cap[c['cscode']] -= next_allot
                
                if to_allot > 0: # try again with relaxed constraints and more capacity at centers 
                    expanded_centers = self.centers_within_distance(s, centers, ABS_DISTANCE_THRESHOLD)
                    for c in expanded_centers:
                        if self.is_allocated(c['cscode'], s['scode']):
                            continue
                        stretched_capacity = math.floor(int(c['capacity']) * STRETCH_CAPACITY_FACTOR + centers_remaining_cap[c['cscode']])
                        next_allot = min(to_allot, max(stretched_capacity, MIN_STUDENT_IN_CENTER))
                        if to_allot > 0 and next_allot > 0 and stretched_capacity >= next_allot:
                            allocated_centers[c['cscode']] = c
                            self.allocate(s['scode'], c['cscode'], next_allot)
                            # allocation.writerow([s['scode'], s['name-address'], c['cscode'], c['name'], c['address'], next_allot, c['distance_km']])
                            to_allot -= next_allot
                            centers_remaining_cap[c['cscode']] -= next_allot

                for c in allocated_centers.values():
                    allocation_file.writerow([s['scode'], s['name-address'], c['cscode'], c['name'], c['address'], self.allocations[s['scode']][c['cscode']], c['distance_km']])

                if to_allot > 0: 
                    remaining+=to_allot
                    self.logger.warning(f"{to_allot}/{s['count']} left for {s['scode']} {s['name-address']} centers: {len(centers_for_school)}")
                        

            self.logger.info("Remaining capacity at each center (remaining_capacity cscode):")
            self.logger.info(sorted([(v,k) for k, v in centers_remaining_cap.items() if v != 0]))
            self.logger.info(f"Total remaining capacity across all centers: {sum({k:v for k, v in centers_remaining_cap.items() if v != 0}.values())}")
            self.logger.info(f"Students not assigned: {remaining}")

centersAllocation = CentersAllocation()
centersAllocation.start_allocation()