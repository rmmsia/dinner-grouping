import os
import pytest
import pandas as pd
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from patcher import patch_matrix, parse_groups_csv


# Sample data of a pairing scores matrix containing 10 members
# Scores range from 0 to 4 where:
# 0 = never met
# 1-4 = increasing levels of familiarity
@pytest.fixture
def test_matrix():
    df = pd.DataFrame({
        'Alice': [0, 1, 0, 3, 2, 0, 1, 0, 4, 0],
        'Bob': [1, 0, 2, 0, 1, 0, 0, 3, 0, 1],
        'Charlie': [0, 2, 0, 1, 0, 4, 0, 1, 0, 3],
        'David': [3, 0, 1, 0, 2, 0, 1, 0, 2, 0],
        'Eve': [2, 1, 0, 2, 0, 3, 0, 0, 1, 0],
        'Frank': [0, 0, 4, 0, 3, 0, 2, 0, 0, 1],
        'Grace': [1, 0, 0, 1, 0, 2, 0, 3, 0, 4],
        'Harry': [0, 3, 1, 0, 0, 0, 3, 0, 2, 0],
        'Ivy': [4, 0, 0, 2, 1, 0, 0, 2, 0, 1],
        'Jack': [0, 1, 3, 0, 0, 1, 4, 0, 1, 0]
    }, index=['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Harry', 'Ivy', 'Jack'])
    return df

@pytest.fixture
def test_groups():
    # Define some existing groups for testing
    return [
        ['Alice', 'Bob', 'Charlie'],  # Group 1
        ['David', 'Eve', 'Frank'],    # Group 2
        ['Grace', 'Harry', 'Ivy', 'Jack'] # Group 3
    ]

def test_patch_matrix(test_matrix, test_groups):
    # Test patch with value of 1
    patch_value = 1
    result_df = patch_matrix(test_matrix, test_groups, patch_value)
    
    # Ideal result after patching
    assert_df = pd.DataFrame({
        'Alice': [0, 2, 1, 3, 2, 0, 1, 0, 4, 0],
        'Bob': [2, 0, 3, 0, 1, 0, 0, 3, 0, 1],
        'Charlie': [1, 3, 0, 1, 0, 4, 0, 1, 0, 3],
        'David': [3, 0, 1, 0, 3, 1, 1, 0, 2, 0],
        'Eve': [2, 1, 0, 3, 0, 4, 0, 0, 1, 0],
        'Frank': [0, 0, 4, 1, 4, 0, 2, 0, 0, 1],
        'Grace': [1, 0, 0, 1, 0, 2, 0, 4, 1, 5],
        'Harry': [0, 3, 1, 0, 0, 0, 4, 0, 3, 1],
        'Ivy': [4, 0, 0, 2, 1, 0, 1, 3, 0, 2],
        'Jack': [0, 1, 3, 0, 0, 1, 5, 1, 2, 0]
    }, index=['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Harry', 'Ivy', 'Jack'])

    # Verify the result
    pd.testing.assert_frame_equal(result_df, assert_df)

    # Verify matrix is still symmetric
    for i in result_df.index:
        for j in result_df.columns:
            assert result_df.loc[i, j] == result_df.loc[j, i]


def test_parse_groups_csv():
    # Create a test CSV and verify correct parsing
    with tempfile.NamedTemporaryFile(suffix='.csv', mode='w+', delete=False) as f:
        f.write("group,telegram_id\n1,user1\n1,user2\n2,user3\n2,user4\n")
        f.flush()
    
    groups = parse_groups_csv(f.name)
    os.unlink(f.name)
    
    assert len(groups) == 2
    assert set(groups[0]) == {'user1', 'user2'}
    assert set(groups[1]) == {'user3', 'user4'}