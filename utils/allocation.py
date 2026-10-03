"""Helpers for the allocation of students to centers."""

from typing import Dict


def merge_small_allocations(
    allocation: Dict[str, int], spare: Dict[str, int], minimum: int
) -> Dict[str, str]:
    """
    Find the allocations of one school that are too small and where to move them.

    allocation: cscode -> students of the school at that center, most preferred first
    spare: cscode -> how many more students the center can take, stretched capacity included
    minimum: fewest students a school should have at a center

    A school with 207 students allocated as 100 + 100 + 7 gets 107 + 100 instead.
    Students are only moved to another center of the same school that has room for them,
    preferably one that already has the minimum and is more preferred. An allocation that
    no other center can take stays as it is. A school with fewer students than the minimum
    is left alone, it can not do any better.

    Returns {small center: center to move its students to}, nothing is changed here.
    """
    if sum(allocation.values()) < minimum:
        return {}
    spare = dict(spare)
    students = dict(allocation)
    order = {cscode: i for i, cscode in enumerate(allocation)}
    moves: Dict[str, str] = {}
    for small in sorted(allocation, key=lambda c: students[c]):
        if students[small] >= minimum or small in moves:
            continue
        targets = [
            c
            for c in allocation
            if c != small and c not in moves and spare[c] >= students[small]
        ]
        if not targets:
            continue
        target = min(targets, key=lambda c: (students[c] < minimum, order[c]))
        moves[small] = target
        students[target] += students[small]
        spare[target] -= students[small]
        students[small] = 0
    return moves
