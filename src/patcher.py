from algo_v2 import Attendee, Group
from loaders import load_attendees, parse_groups_txt

def patch_matrix(pairing_scores, groups_path, patch_value):
    '''
    pairing_scores: pd.DataFrame (pairing scores matrix)
    groups_path: str (path to the groups txt file which should have telegram IDs)
    patch_value: int (value to increment the pairing scores by)
    '''
    groups = parse_groups_txt(groups_path)
    for group in groups:
        for i, member1 in enumerate(group):
            for member2 in group[i + 1:]:
                # Update the pairing scores matrix
                pairing_scores.loc[member1, member2] += patch_value
                pairing_scores.loc[member2, member1] += patch_value
    return pairing_scores