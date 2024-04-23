OUTPUT_DIR = 'results/'
CENTER_DISTANCE_OUTPUT_FILE = 'school-center-distance.tsv'

PREF_DISTANCE_THRESHOLD = 2  # Preferred threshold distance in kilometers
ABS_DISTANCE_THRESHOLD = 7  # Absolute threshold distance in kilometers
MIN_STUDENT_IN_CENTER = 10  # minimum number of students from a school to be assigned to a center in normal circumstances
STRETCH_CAPACITY_FACTOR = 0.02  # how much can center capacity be streched if need arises
PREF_CUTOFF = -4 # Do not allocate students with pref score less than cutoff

EARTH_RADIUS = 6371