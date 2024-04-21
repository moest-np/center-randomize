import argparse
import csv
import math
import os
import random
from collections.abc import Iterable, Mapping
from typing import Any, Final

OUTPUT_DIR: Final = "results"

PREF_DISTANCE_THRESHOLD: Final = 2  # Preferred threshold distance in kilometers
ABS_DISTANCE_THRESHOLD: Final = 7  # Absolute threshold distance in kilometers
MIN_STUDENT_IN_CENTER: Final = 10  # minimum number of students from a school to be assigned to a center in normal circumstances
STRETCH_CAPACITY_FACTOR: Final = (
    0.02  # how much can center capacity be streched if need arises
)
PREF_CUTOFF: Final = -4  # Do not allocate students with pref score less than cutoff


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points
    on the earth specified in decimal degrees.

    Args:
    ----
        lat1: The latitude of the first point in decimal degrees.
        lon1: The longitude of the first point in decimal degrees.
        lat2: The latitude of the second point in decimal degrees.
        lon2: The longitude of the second point in decimal degrees.

    Returns:
    -------
        The distance between the two points in kilometers.

    """
    RADIUS_EARTH: Final = 6371  # Radius of Earth in kilometers

    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return RADIUS_EARTH * c


def centers_within_distance(
    preferences: Mapping[str, Mapping[str, int]],
    school: Mapping[str, str],
    centers: Iterable[Mapping[str, str]],
    distance_threshold: float,
) -> list[dict[str, Any]]:
    """Return List of centers that are within given distance from school.
        If there are no centers within given distance return one that is closest.

    Args:
    ----
        preferences: The preferences of the schools
        school: The school that needs to be assigned
        centers: The plausible centers
        distance_threshold: The distance threshold

    Returns:
    -------
        Return List of centers that are within given distance from school.
        Returned params :
            {'cscode', 'name', 'address', 'capacity', 'lat', 'long', 'distance_km'}.

    """

    def center_to_dict(c: Mapping[str, str], distance: float) -> dict[str, str | float]:
        required_keys: Final = {"cscode", "name", "address", "capacity", "lat", "long"}
        return_dict: dict[str, str | float] = {
            k: v for k, v in c.items() if k in required_keys
        }
        return_dict["distance_km"] = distance

        return return_dict

    def sort_key(c: Mapping[str, Any]) -> float:
        # intent: sort by preference score DESC then by distance_km ASC
        # leaky abstraction - sorted requires a single numberic value for each element
        return (
            c["distance_km"] * random.uniform(1, 5)
            - get_pref(preferences, school["scode"], c["cscode"]) * 100
        )

    raw_school_lat = school.get("lat")

    if not raw_school_lat:
        print(f"Latitude is not found for scode: {school['scode']}")
        return []

    try:
        school_lat = float(raw_school_lat)
    except ValueError:
        print(f"Latitude is not a number for scode: {school['scode']}")
        return []

    raw_school_long = school.get("long")

    if not raw_school_long:
        print(f"Longitude is not found for scode: {school['scode']}")
        return []

    try:
        school_long = float(raw_school_long)
    except ValueError:
        print(f"Longitude is not a number for scode: {school['scode']}")
        return []

    within_distance = []
    nearest_distance = float("inf")
    nearest_center = None

    for c in centers:
        if school.get("scode") == c.get("cscode"):
            continue

        raw_center_lat = c.get("lat")

        if not raw_center_lat:
            print(f"Latitude is not found for ccode: {c['cscode']}")
            continue

        try:
            center_lat = float(raw_center_lat)
        except ValueError:
            print(f"Latitude is not a number for ccode: {c['cscode']}")
            continue

        raw_center_long = c.get("long")

        if not raw_center_long:
            print(f"Longitude is not found for ccode: {c['cscode']}")
            continue

        try:
            center_long = float(raw_center_long)
        except ValueError:
            print(f"Longitude is not a number for ccode: {c['cscode']}")
            continue

        distance = haversine_distance(
            school_lat,
            school_long,
            center_lat,
            center_long,
        )

        if nearest_center is None or distance < nearest_distance:
            nearest_center = c
            nearest_distance = distance

        if (
            distance <= distance_threshold
            and get_pref(preferences, school["scode"], c["cscode"]) > PREF_CUTOFF
        ):
            within_distance.append(center_to_dict(c, distance))

    if within_distance:
        return sorted(within_distance, key=sort_key)

    # if there are no centers within given  threshold, return one that is closest
    if nearest_center is not None:
        return [center_to_dict(nearest_center, nearest_distance)]

    # If the loop didn't run fallback to empty list
    return []


def read_tsv(file_path: str | os.PathLike) -> list[dict[str, str]]:
    """Reads tsv file and returns list of dictionaries.

    Args:
    ----
        file_path: The path of the tsv file

    Returns:
    -------
        List of dictionaries

    """
    data = []
    with open(file_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter="\t")
        for row in reader:
            data.append(row)
    return data


def read_prefs(file_path: str | os.PathLike) -> dict[str, dict[str, int]]:
    """Reads the preferences file and returns a dictionary.

    Args:
    ----
        file_path: The path of the tsv file

    Returns:
    -------
        Dictionary with the school code as the key and the dictionary of
        the center code and preference score as the value

    """
    prefs: dict[str, dict[str, int]] = {}
    with open(file_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter="\t")
        for row in reader:
            scode = row.get("scode")
            if not scode:
                continue

            cscode = row.get("cscode")
            if not cscode:
                continue

            raw_curr_pref = row.get("pref")

            if not raw_curr_pref:
                continue

            try:
                curr_pref = int(raw_curr_pref)
            except ValueError:
                continue

            school_pref = prefs.get(scode)
            if school_pref:
                if cscode in school_pref:
                    school_pref[cscode] += curr_pref
                else:
                    school_pref[cscode] = curr_pref
            else:
                prefs[scode] = {cscode: curr_pref}

    return prefs


def get_pref(
    preferences: Mapping[str, Mapping[str, int]],
    scode: str,
    cscode: str,
) -> int:
    """Returns the preference score of the center for the school.

    Args:
    ----
        preferences: The preferences of the schools
        scode: The school code
        cscode: The center code

    Returns:
    -------
        The preference score of the center for the school

    """
    school_pref = preferences.get(scode)
    if school_pref:
        center_pref = school_pref.get(cscode)
        if center_pref is not None:
            # Just to be a 100% sure that it is a int
            try:
                return int(center_pref)
            except ValueError:
                # If not an intger the last fallback with return 0
                ...
    return 0


def calc_per_center(count: float) -> int:
    if count <= 400:
        return 100
    # if count <= 900:
    #     return 200
    return 200


def school_sort_key(s: Mapping[str, Any]) -> float:
    """Sorts schools by preference score.

    Args:
    ----
        s: The school

    Returns:
    -------
        The preference score of the school

    """
    COUNT_THRESHOLD: Final = 500
    raw_count = s.get("count")

    order = 1
    if raw_count:
        try:
            count = int(raw_count)
        except ValueError:
            ...
        else:
            # Chaange only if the count is an int which is too high
            if count > COUNT_THRESHOLD:
                order = -1

    return order * random.uniform(1, 100)


def allocate(
    allocations: dict[str, dict[str, int]],
    scode: str,
    cscode: str,
    count: int,
) -> Mapping[str, Mapping[str, int]]:
    """Allocates a center to a school.
    Performs inplace updates the returns the same dictionary.

    Args:
    ----
        allocations: The current allocations
        scode: The school code
        cscode: The center code
        count: The number of students

    Returns:
    -------
        The updated allocations

    """
    school_alloc = allocations.get(scode)
    if school_alloc is None:
        allocations[scode] = {cscode: count}
    elif cscode in school_alloc:
        school_alloc[cscode] += count
    else:
        school_alloc[cscode] = count

    return allocations


def is_allocated(
    allocations: Mapping[str, Iterable[str]],
    scode: str,
    cscode: str,
) -> bool:
    """Checks if center is allocated to school.

    Args:
    ----
        allocations: The current allocations
        scode: The school code
        cscode: The center code

    Returns:
    -------
        True if the center is allocated to the school

    """
    return cscode in allocations.get(scode, ())


def main(args: argparse.Namespace) -> None:
    """The main function.

    Args:
    ----
        args: The command line arguments

    """
    schools = sorted(read_tsv(args.schools_tsv), key=school_sort_key)
    centers = read_tsv(args.centers_tsv)
    centers_remaining_cap = {c["cscode"]: int(c["capacity"]) for c in centers}
    prefs = read_prefs(args.prefs_tsv)

    remaining = 0  # stores count of non allocated students
    allocations: dict[str, dict[str, int]] = {}  # to track mutual allocations

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with (
        open(
            os.path.join(OUTPUT_DIR, "school-center-distance.tsv"),
            "w",
            encoding="utf-8",
        ) as intermediate_file,
        open(os.path.join(OUTPUT_DIR, args.output), "w", encoding="utf-8") as a_file,
    ):
        writer = csv.writer(intermediate_file, delimiter="\t")
        writer.writerow(
            (
                "scode",
                "s_count",
                "school_name",
                "school_lat",
                "school_long",
                "cscode",
                "center_name",
                "center_address",
                "center_capacity",
                "distance_km",
            ),
        )

        allocation_file = csv.writer(a_file, delimiter="\t")
        allocation_file.writerow(
            (
                "scode",
                "school",
                "cscode",
                "center",
                "center_address",
                "allocation",
                "distance_km",
            ),
        )

        for s in schools:
            centers_for_school = centers_within_distance(
                prefs,
                s,
                centers,
                PREF_DISTANCE_THRESHOLD,
            )
            raw_to_allot = s.get("count")

            if not raw_to_allot:
                continue

            try:
                to_allot = int(raw_to_allot)
            except ValueError:
                continue

            per_center = calc_per_center(to_allot)

            allocated_centers = {}

            # per_center = math.ceil(to_allot / min(calc_num_centers(to_allot), len(centers_for_school)))
            for c in centers_for_school:
                writer.writerow(
                    [
                        s["scode"],
                        s["count"],
                        s["name-address"],
                        s["lat"],
                        s["long"],
                        c["cscode"],
                        c["name"],
                        c["address"],
                        c["capacity"],
                        c["distance_km"],
                    ],
                )

                if is_allocated(allocated_centers, c["cscode"], s["scode"]):
                    continue

                next_allot = min(
                    to_allot,
                    per_center,
                    max(centers_remaining_cap[c["cscode"]], MIN_STUDENT_IN_CENTER),
                )
                if (
                    to_allot > 0
                    and next_allot > 0
                    and centers_remaining_cap[c["cscode"]] >= next_allot
                ):
                    allocated_centers[c["cscode"]] = c
                    allocate(allocations, s["scode"], c["cscode"], next_allot)
                    # allocation.writerow([s['scode'], s['name-address'], c['cscode'], c['name'], c['address'], next_allot, c['distance_km']])
                    to_allot -= next_allot
                    centers_remaining_cap[c["cscode"]] -= next_allot

            if (
                to_allot > 0
            ):  # try again with relaxed constraints and more capacity at centers
                expanded_centers = centers_within_distance(
                    prefs,
                    s,
                    centers,
                    ABS_DISTANCE_THRESHOLD,
                )
                for c in expanded_centers:
                    if is_allocated(allocations, c["cscode"], s["scode"]):
                        continue

                    stretched_capacity = math.floor(
                        int(c["capacity"]) * STRETCH_CAPACITY_FACTOR
                        + centers_remaining_cap[c["cscode"]],
                    )
                    next_allot = min(
                        to_allot,
                        max(stretched_capacity, MIN_STUDENT_IN_CENTER),
                    )
                    if (
                        to_allot > 0
                        and next_allot > 0
                        and stretched_capacity >= next_allot
                    ):
                        allocated_centers[c["cscode"]] = c
                        allocate(allocations, s["scode"], c["cscode"], next_allot)
                        # allocation.writerow([s['scode'], s['name-address'], c['cscode'], c['name'], c['address'], next_allot, c['distance_km']])
                        to_allot -= next_allot
                        centers_remaining_cap[c["cscode"]] -= next_allot

            for c in allocated_centers.values():
                allocation_file.writerow(
                    [
                        s["scode"],
                        s["name-address"],
                        c["cscode"],
                        c["name"],
                        c["address"],
                        allocations[s["scode"]][c["cscode"]],
                        c["distance_km"],
                    ],
                )

            if to_allot > 0:
                remaining += to_allot
                print(
                    f"{to_allot}/{s['count']} left for {s['scode']} {s['name-address']} centers: {len(centers_for_school)}",
                )

        print("Remaining capacity at each center (remaining_capacity cscode):")
        print(sorted([(v, k) for k, v in centers_remaining_cap.items() if v != 0]))
        print(
            f"Total remaining capacity across all centers: {sum({k:v for k, v in centers_remaining_cap.items() if v != 0}.values())}",
        )
        print(f"Students not assigned: {remaining}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="center randomizer",
        description="Assigns centers to exam centers to students",
    )
    parser.add_argument(
        "schools_tsv",
        default="schools.tsv",
        help="Tab separated (TSV) file containing school details",
    )
    parser.add_argument(
        "centers_tsv",
        default="centers.tsv",
        help="Tab separated (TSV) file containing center details",
    )
    parser.add_argument(
        "prefs_tsv",
        default="prefs.tsv",
        help="Tab separated (TSV) file containing preference scores",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="school-center.tsv",
        help="Output file",
    )
    args = parser.parse_args()

    main(args)
