import os

PREF_DISTANCE_THRESHOLD = 2  # Preferred threshold distance in kilometers
ABS_DISTANCE_THRESHOLD = 7  # Absolute threshold distance in kilometers
MIN_STUDENT_IN_CENTER = 10  # minimum number of students from a school to be assigned to a center in normal circumstances
STRETCH_CAPACITY_FACTOR = 0.02  # how much can center capacity be streched if need arises
PREF_CUTOFF = -4 # Do not allocate students with pref score less than cutoff
BASE_DIR=os.path.dirname(os.path.abspath(__file__))
SCHOOLS_TSV = f"{BASE_DIR}/sample_data/schools_grade12_2081.tsv"
CENTERS_TSV = f"{BASE_DIR}/sample_data/centers_grade12_2081.tsv"
PREFS_TSV = f"{BASE_DIR}/sample_data/prefs.tsv"
OUTPUT_DIR=f"{BASE_DIR}/results"
OUTPUT_TSV=f"{OUTPUT_DIR}/school_center_allocation.tsv"
DISTANCE_TSV=f"{OUTPUT_DIR}/school_center_distance.tsv"
