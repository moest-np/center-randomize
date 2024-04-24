import argparse
import logging
import random
import csv
from pathlib import Path
from utils import (
    configure_logging,
    read_tsv,
    read_prefs,
    allocate_students,
    calculate_remaining_capacity
)

configure_logging()
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        prog='center_randomizer',
        description='Assigns centers to exam centers to students'
    )
    parser.add_argument('schools_tsv', help="Path to the schools TSV file")
    parser.add_argument('centers_tsv', help="Path to the centers TSV file")
    parser.add_argument('prefs_tsv', help="Path to the preferences TSV file")
    parser.add_argument('-o', '--output', default='school-center.tsv', help='Output file path')
    parser.add_argument('-s', '--seed', metavar='SEED', type=int, help='Seed for Random Number Generator')

    args = parser.parse_args()

    # Seed the random number generator
    random.seed(args.seed) if args.seed else random.seed()

    try:
        # Read input data
        schools = read_tsv(args.schools_tsv)
        centers = read_tsv(args.centers_tsv)
        prefs = read_prefs(args.prefs_tsv)

        # Allocate students to centers
        remaining_capacity = {c['cscode']: int(c['capacity']) for c in centers}
        remaining_students = allocate_students(schools, centers, prefs, remaining_capacity)

        # Write allocation results to output file
        output_dir = Path('results')
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / args.output

        with open(output_path, 'w', newline='', encoding='utf-8') as allocation_file:
            writer = csv.writer(allocation_file, delimiter='\t')
            writer.writerow(["scode", "school", "cscode", "center", "center_address", "allocation", "distance_km"])

            for school_code, allocations in remaining_students.items():
                for center_code, allocation in allocations.items():
                    writer.writerow([school_code, allocation['school'], center_code, allocation['center'],
                                     allocation['center_address'], allocation['allocation'], allocation['distance_km']])

        # Log remaining capacity and unassigned students
        logger.info(f"Remaining capacity at each center: {calculate_remaining_capacity(remaining_capacity)}")
        logger.info(f"Students not assigned: {sum(remaining_students.values())}")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e.filename}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
