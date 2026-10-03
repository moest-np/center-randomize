import csv
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHOOLS = os.path.join(ROOT, "sample_data", "schools_grade12_2081.tsv")
CENTERS = os.path.join(ROOT, "sample_data", "centers_grade12_2081.tsv")
PREFS = os.path.join(ROOT, "sample_data", "prefs.tsv")
SEEDS = range(1, 21)


def run_script(output, *args, inputs=(SCHOOLS, CENTERS, PREFS)):
    """Run school_center.py, return the finished process and the not assigned students."""
    process = subprocess.run(
        [sys.executable, os.path.join(ROOT, "school_center.py"), *inputs,
         "-o", str(output), *args],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    match = re.search(r"Students not assigned: (\d+)", process.stdout)
    return process, int(match.group(1)) if match else None


def read_rows(output):
    with open(output, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file, delimiter="\t"))


def write_tsv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)
    return str(path)


def tiny_inputs(tmp_path, schools, capacities, no_coordinates=()):
    """
    Schools, as a number of students for one school or a list of (scode, students),
    and centers with the given capacities, all within 1 km of the schools.
    """
    if isinstance(schools, int):
        schools = [("1", schools)]
    schools = write_tsv(
        tmp_path / "schools.tsv", ["scode", "count", "name-address", "lat", "long"],
        [[scode, students, f"School {scode}"] + (["", ""] if scode in no_coordinates else ["27.7000", "85.3000"])
         for scode, students in schools])
    centers = write_tsv(
        tmp_path / "centers.tsv", ["cscode", "capacity", "name", "address", "lat", "long"],
        [[str(100 + i), capacity, f"Center {i}", "addr", f"27.70{i + 1}", "85.3000"]
         for i, capacity in enumerate(capacities)])
    prefs = write_tsv(tmp_path / "prefs.tsv", ["scode", "cscode", "pref", "reason"], [])
    return (schools, centers, prefs)


def seed_that_needs_a_retry(tmp_path):
    """First seed for which the first attempt leaves students, and how many it leaves."""
    for seed in SEEDS:
        _, left = run_script(tmp_path / "probe" / "school-center.tsv", "-s", str(seed), "-a", "1")
        if left:
            return seed, left
    pytest.fail("every seed works at the first attempt, the test needs another data set")


def test_students_left_without_a_center_are_allocated_in_a_new_attempt(tmp_path):
    seed, left = seed_that_needs_a_retry(tmp_path)
    assert left > 0
    process, left = run_script(tmp_path / "out" / "school-center.tsv", "-s", str(seed), "-a", "10")
    assert left == 0
    assert "Attempt 1/10" in process.stdout
    allocated = sum(int(row["allocation"]) for row in read_rows(tmp_path / "out" / "school-center.tsv"))
    wanted = sum(int(row["count"]) for row in read_rows(SCHOOLS))
    assert allocated == wanted


def test_same_seed_gives_the_same_result_when_retrying(tmp_path):
    seed, _ = seed_that_needs_a_retry(tmp_path)
    run_script(tmp_path / "a" / "school-center.tsv", "-s", str(seed))
    run_script(tmp_path / "b" / "school-center.tsv", "-s", str(seed))
    assert read_rows(tmp_path / "a" / "school-center.tsv") == read_rows(tmp_path / "b" / "school-center.tsv")


def test_a_successful_first_attempt_is_kept_without_retrying(tmp_path):
    for seed in SEEDS:
        process, left = run_script(tmp_path / "one" / "school-center.tsv", "-s", str(seed), "-a", "1")
        if left == 0:
            break
    else:
        pytest.fail("no seed works at the first attempt, the test needs another data set")
    process, left = run_script(tmp_path / "default" / "school-center.tsv", "-s", str(seed))
    assert left == 0 and "Attempt" not in process.stdout
    assert "still not assigned" not in process.stdout + process.stderr
    assert read_rows(tmp_path / "one" / "school-center.tsv") == read_rows(tmp_path / "default" / "school-center.tsv")


def test_all_attempts_are_reported_and_the_result_is_still_written(tmp_path):
    # 100 students but the only center has 50 seats and can not be stretched enough
    inputs = tiny_inputs(tmp_path, 100, [50])
    out = tmp_path / "out" / "school-center.tsv"
    process, left = run_script(out, "-a", "3", inputs=inputs)
    assert left == 50
    assert "Attempt 1/3: 50 students not assigned, trying again" in process.stdout
    assert "Attempt 3/3: 50 students not assigned" in process.stdout
    assert "Attempt 3/3: 50 students not assigned, trying again" not in process.stdout
    assert "50 students are still not assigned to a center after 3 attempts" in process.stderr
    assert [row["allocation"] for row in read_rows(out)] == ["50"]


def test_the_best_attempt_is_kept_even_if_it_is_not_the_last(tmp_path):
    # One center with 102 seats (stretched) for schools of 95 and 30 students: 25 or 30
    # students are left, depending on which school comes first
    inputs = tiny_inputs(tmp_path, [("1", 95), ("2", 30)], [100])
    for seed in range(1, 16):
        out = tmp_path / f"out{seed}" / "school-center.tsv"
        process, left = run_script(out, "-s", str(seed), "-a", "3", inputs=inputs)
        tried = {int(i): int(n) for i, n in re.findall(r"Attempt (\d)/3: (\d+) students", process.stdout)}
        assert left == min(tried.values())
        assert sum(int(row["allocation"]) for row in read_rows(out)) == 125 - left
        if tried[3] > left:
            # the best attempt was written and the log says which one it was
            assert re.search(r"Result of attempt \d of 3 kept", process.stdout)
            return
    pytest.fail("no seed has a best attempt before the last one, the test needs another data set")


def test_attempts_stop_when_the_remaining_students_can_never_be_placed(tmp_path):
    # School 2 has no coordinates, so no attempt can give it a center
    inputs = tiny_inputs(tmp_path, [("1", 40), ("2", 20)], [500], no_coordinates=("2",))
    process, left = run_script(tmp_path / "out" / "school-center.tsv", "-a", "10", inputs=inputs)
    assert left == 20
    assert "Attempt" not in process.stdout
    assert "20 students are still not assigned to a center after 1 attempt." in process.stderr


def test_duplicate_school_code_does_not_crash(tmp_path):
    # Not a valid input, but it used to give a KeyError when small allocations were merged
    inputs = tiny_inputs(tmp_path, [("1", 107), ("1", 50)], [100, 7, 300])
    for seed in range(1, 7):
        process, _ = run_script(tmp_path / f"out{seed}" / "school-center.tsv", "-s", str(seed), inputs=inputs)
        assert process.returncode == 0, process.stderr


@pytest.mark.parametrize("attempts", ["0", "-1"])
def test_max_attempts_must_be_positive(tmp_path, attempts):
    process, _ = run_script(tmp_path / "out" / "school-center.tsv", "-a", attempts)
    assert process.returncode == 2
    assert "--max-attempts must be at least 1" in process.stderr


def test_small_remainder_is_added_to_another_center_of_the_school(tmp_path):
    # 207 students are split 100 + 100 + 7 at first, 7 is below MIN_STUDENT_IN_CENTER
    inputs = tiny_inputs(tmp_path, 207, [500, 500, 500])
    out = tmp_path / "out" / "school-center.tsv"
    process, left = run_script(out, "-s", "1", inputs=inputs)
    assert left == 0
    assert sorted(int(row["allocation"]) for row in read_rows(out)) == [100, 107]


def test_small_remainder_stays_when_no_other_center_has_room(tmp_path):
    # Three full centers of 100 seats can only take 2 more students each (stretched capacity)
    inputs = tiny_inputs(tmp_path, 207, [100, 100, 100])
    out = tmp_path / "out" / "school-center.tsv"
    process, left = run_script(out, "-s", "1", inputs=inputs)
    assert left == 0
    assert sorted(int(row["allocation"]) for row in read_rows(out)) == [7, 100, 100]


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_no_center_gets_more_students_than_its_stretched_capacity(tmp_path, seed):
    out = tmp_path / "out" / "school-center.tsv"
    run_script(out, "-s", str(seed))
    capacity = {row["cscode"]: int(row["capacity"]) for row in read_rows(CENTERS)}
    students = {}
    for row in read_rows(out):
        students[row["cscode"]] = students.get(row["cscode"], 0) + int(row["allocation"])
    too_many = {c: n for c, n in students.items() if n > capacity[c] + int(capacity[c] * 0.02)}
    assert not too_many
