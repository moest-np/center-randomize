import math
def filter_dict_with_non_zero_values(d:dict)->dict:
        return {k: v for k, v in d.items() if v != 0}
def sort_dict_by_value(d:dict)->dict:
        return dict(sorted(d.items(), key=lambda item: item[1]))

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth specified in decimal degrees
    """
    RADIUS_EARTH = 6371  # Radius of Earth in kilometers
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = RADIUS_EARTH * c
    return distance
