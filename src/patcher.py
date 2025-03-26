import pandas as pd
from algo_v2 import Attendee, Group
from loaders import load_attendees, parse_groups_txt

def parse_groups_csv(groups_csv_path):
    """
    Parse a CSV file containing group assignments into a list of lists of telegram_ids

    Args:
        groups_csv_path (str): Path to the CSV file containing group assignments

    Returns:
        List[List[str]]: List of groups, where each group is a list of telegram_ids
    """
    df = pd.read_csv(groups_csv_path)

    # Check if 'Group' column exists
    if 'group' not in df.columns:
        raise ValueError("CSV file must contain a 'Group' column")

    # Check if it contains telegram_id column
    id_column = None
    for col in ['telegram_id', 'Telegram ID', 'Telegram', 'ID']:
        if col in df.columns:
            id_column = col
            break

    if id_column is None:
        raise ValueError("CSV file must contain a column with IDs (telegram_id, Telegram ID)")

    # Group by Group column and collect IDs
    groups = []
    for _, group_df in df.groupby('group'):
        group = group_df[id_column].tolist()
        # Remove NaN values
        group = [str(id_val).strip() for id_val in group if pd.notna(id_val)]
        if group:  # Only add non-empty groups
            groups.append(group)

    return groups

def patch_matrix(pairing_scores, groups, patch_value):
    '''
    pairing_scores: pd.DataFrame (pairing scores matrix)
    groups: List[List[str]] (list of groups, where each group is a list of telegram_ids)
    patch_value: int (value to increment the pairing scores by)
    '''
    result = pairing_scores.copy()
    print("Patching pairing scores matrix...")
    for group in groups:
        for i, member1 in enumerate(group):
            for member2 in group[i + 1:]:
                # Update the pairing scores matrix
                result.loc[member1, member2] += patch_value
                result.loc[member2, member1] += patch_value
    return result
