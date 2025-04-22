import pytest
import pandas as pd
import sys
import os
from collections import namedtuple, defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import algo_v2 as al



@pytest.mark.parametrize("num_attendees, max_size, expected", [
    (10, 5, [5, 5]),
    (11, 5, [4, 4, 3]),
    (3, 5, [3]),
    (15, 5, [5, 5, 5]),
    (1, 5, [1]),
    (4, 1, [1, 1, 1, 1]),
    (23, 5, [5, 5, 5, 4, 4]),
    (14, 5, [5, 5, 4]),
    (7, 3, [3, 2, 2]),
    (0, 5, []),
])
def test_determine_group_size(num_attendees, max_size, expected):
    assert al.determine_group_size(num_attendees, max_size) == expected


Member = namedtuple("Member", ["gender", "year", "faculty"])

@pytest.mark.parametrize("candidate, group, weights, expected", [
    # Empty group → 1.0 per category → total = 1.0 (sum of weights)
    (
        Member("M", 1, "Engineering"),
        [],
        {'gender': 1/3, 'year': 1/3, 'faculty': 1/3},
        1.0
    ),

    # All categories have 1 match → 1 / (1 + 1) = 0.5 each
    (
        Member("F", 2, "Arts"),
        [Member("F", 2, "Arts")],
        {'gender': 1/3, 'year': 1/3, 'faculty': 1/3},
        1/3 * 0.5 + 1/3 * 0.5 + 1/3 * 0.5  # = 0.5
    ),

    # Gender match only → 0.5 + 1 + 1 weighted
    (
        Member("M", 3, "Law"),
        [Member("M", 2, "Arts")],
        {'gender': 0.4, 'year': 0.3, 'faculty': 0.3},
        0.4 * 0.5 + 0.3 * 1.0 + 0.3 * 1.0  # = 0.2 + 0.3 + 0.3 = 0.8
    ),

    # Weighted: heavily prioritize faculty (0.6), rest small
    (
        Member("F", 2, "Engineering"),
        [Member("F", 2, "Engineering")],
        {'gender': 0.2, 'year': 0.2, 'faculty': 0.6},
        0.2 * 0.5 + 0.2 * 0.5 + 0.6 * 0.5  # = 0.1 + 0.1 + 0.3 = 0.5
    ),

    # New candidate in all categories → 1.0 each, weighted
    (
        Member("X", 4, "Medicine"),
        [Member("M", 1, "Law"), Member("F", 2, "Engineering")],
        {'gender': 0.2, 'year': 0.3, 'faculty': 0.5},
        0.2 * 1.0 + 0.3 * 1.0 + 0.5 * 1.0  # = 1.0
    ),
])
def test_calc_diversity_score(candidate, group, weights, expected):
    assert al.calc_diversity_score(candidate, group, weights) == pytest.approx(expected)