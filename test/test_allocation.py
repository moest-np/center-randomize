import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.allocation import merge_small_allocations

MINIMUM = 10
ROOM = {"A": 50, "B": 50, "C": 50, "D": 50}


def test_small_remainder_is_added_to_the_first_center():
    # 207 students as 100 + 100 + 7 -> 107 + 100
    allocation = {"A": 100, "B": 100, "C": 7}
    assert merge_small_allocations(allocation, ROOM, MINIMUM) == {"C": "A"}


def test_nothing_to_do_when_all_allocations_reach_the_minimum():
    allocation = {"A": 100, "B": 10, "C": 57}
    assert merge_small_allocations(allocation, ROOM, MINIMUM) == {}


def test_remainder_stays_when_no_center_has_room_for_it():
    allocation = {"A": 100, "B": 100, "C": 7}
    spare = {"A": 6, "B": 0, "C": 0}
    assert merge_small_allocations(allocation, spare, MINIMUM) == {}


def test_next_center_with_room_is_used():
    allocation = {"A": 100, "B": 100, "C": 7}
    spare = {"A": 6, "B": 7, "C": 0}
    assert merge_small_allocations(allocation, spare, MINIMUM) == {"C": "B"}


def test_center_that_already_has_the_minimum_is_preferred_as_target():
    # B is more preferred than A, but has only 5 students itself
    allocation = {"B": 5, "A": 100, "C": 3}
    moves = merge_small_allocations(allocation, ROOM, MINIMUM)
    assert moves == {"C": "A", "B": "A"}


def test_two_small_allocations_may_end_up_together():
    # 4 + 5 is still below the minimum, but 6 + 5 + 4 is not: only one move needed
    allocation = {"A": 6, "B": 5, "C": 4}
    spare = {"A": 0, "B": 5, "C": 0}
    assert merge_small_allocations(allocation, spare, MINIMUM) == {"C": "B"}


def test_room_is_not_counted_twice():
    # A has room for B's 4 students or for C's 5, not for both: the smaller goes first
    allocation = {"A": 100, "B": 4, "C": 5}
    spare = {"A": 8, "B": 0, "C": 0}
    assert merge_small_allocations(allocation, spare, MINIMUM) == {"B": "A"}


def test_school_smaller_than_the_minimum_is_left_alone():
    assert merge_small_allocations({"A": 4, "B": 3}, ROOM, MINIMUM) == {}


def test_input_is_not_changed():
    allocation = {"A": 100, "B": 100, "C": 7}
    spare = dict(ROOM)
    merge_small_allocations(allocation, spare, MINIMUM)
    assert allocation == {"A": 100, "B": 100, "C": 7}
    assert spare == ROOM


def test_empty_allocation():
    assert merge_small_allocations({}, {}, MINIMUM) == {}
