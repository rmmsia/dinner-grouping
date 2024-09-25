from grouping import GreedyGroupManager


def parse_groups(filename):
    with open(filename, 'r') as file:
        content = file.read().strip()

    # Split content by double newlines to get groups
    groups = content.split('\n\n')

    # Split each group by single newlines to get individual elements
    list_of_lists = [group.split('\n') for group in groups]

    return list_of_lists


def patch_matrix(csv_path, txt_path, patch_value):
    # Initialise the GreedyGroupManager with the pairing scores matrix
    group_manager = GreedyGroupManager(pairing_scores_file=csv_path)
    groups = parse_groups(txt_path)

    # Patch the matrix scores (using _patch_pairing_scores method)
    group_manager._patch_pairing_scores(groups, float(patch_value))
    group_manager.pairing_scores = group_manager.pairing_scores.astype(int)

    # return the dataframe
    return group_manager.pairing_scores

def update_matrix(csv_path, txt_path):
    group_manager = GreedyGroupManager(pairing_scores_file=csv_path)
    groups = parse_groups(txt_path)

    # Update the matrix scores (using _update_pairing_scores method)
    group_manager._update_pairing_scores(groups)
    print(group_manager.pairing_scores)
    group_manager.pairing_scores = group_manager.pairing_scores.astype(int)

    # Return the dataframe
    return group_manager.pairing_scores
