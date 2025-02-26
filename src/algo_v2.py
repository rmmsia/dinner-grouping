import random
import pandas as pd
import chardet
import qa
from collections import defaultdict

# Global
list_shuffle_seed = random.seed(694519)  # for shuffling attendees (remove bias towards initial list order)
selector_seed = random.Random(42)  # for tiebreaker


class Attendee:
    def __init__(self, name, gender, telegram_id, email, year, faculty):
        self.name = name
        self.gender = gender
        self.telegram_id = telegram_id
        self.email = email
        self.year = year
        self.faculty = faculty

    def __repr__(self):
        return f'{self.name} ({self.email}, {self.telegram_id}, {self.gender}, {self.year}, {self.faculty})'


class Group:
    def __init__(self, group_id, capacity, members):
        self.group_id = None
        self.capacity = capacity
        self.members = members


def determine_group_size(num_attendees, max_size=5):
    g = (num_attendees + max_size - 1) // max_size  # Calculate minimum groups needed
    q, r = divmod(num_attendees, g)  # Compute base size and remainder
    group_sizes = [q + 1] * r + [q] * (g - r)  # First 'r' groups get q+1, rest get q
    return group_sizes


def assign_groups(attendees, matrix, weights):
    print(weights)

    group_sizes = determine_group_size(len(attendees), 5)
    groups = [Group(i, group_size, []) for i, group_size in enumerate(group_sizes, start=1)]
    ungrouped = list(attendees.values())
    random.shuffle(ungrouped)

    for group in groups:
        # Greedily assign members to group, for each group
        while len(group.members) < group.capacity and ungrouped:
            best_candidate = None
            best_score = float('-inf')

            for candidate in ungrouped:
                # Calculate diversity score
                diversity_score = calc_diversity_score(candidate, group.members, weights)

                # Calculate repetition penalty
                repeat_penalty = sum(
                    matrix.loc[candidate.telegram_id, member.telegram_id] for member in group.members
                )

                # Total score
                score = diversity_score - repeat_penalty

                if score > best_score:
                    best_score = score
                    best_candidate = candidate
                # Probabilistic tiebreaker
                elif score == best_score and selector_seed.random() < 0.5:
                    best_candidate = candidate

            if best_candidate:
                group.members.append(best_candidate)
                ungrouped.remove(best_candidate)

    return groups


def calc_diversity_score(candidate, group, weights):
    gender_count = defaultdict(int)
    year_count = defaultdict(int)
    faculty_count = defaultdict(int)

    # Count current group representation
    for member in group:
        gender_count[member.gender] += 1
        year_count[member.year] += 1
        faculty_count[member.faculty] += 1

    # Get candidate's attributes
    gender = candidate.gender
    year = candidate.year
    faculty = candidate.faculty

    # Calculate diversity score
    gender_score = weights['gender'] * (1.0 / (1 + gender_count[gender]))
    year_score = weights['year'] * (1.0 / (1 + year_count[year]))
    faculty_score = weights['faculty'] * (1.0 / (1 + faculty_count[faculty]))

    return gender_score + year_score + faculty_score


def load_pairing_score_matrix(file_path):
    return pd.read_csv(file_path, index_col=0)


def save_pairing_score_matrix(matrix, file_path):
    matrix.to_csv(file_path)


def update_pairing_scores(groups, matrix):
    for group in groups:
        for i, member1 in enumerate(group):
            for member2 in group[i + 1:]:
                # Update the pairing scores matrix
                matrix.loc[member1.name, member2.name] += 1
                matrix.loc[member2.name, member1.name] += 1
    return matrix


def add_new_attendees(new_attendees, matrix):
    for attendee in new_attendees:
        matrix.loc[attendee] = 0
        matrix[attendee] = 0

    return matrix


'''
Main workflow takes in the following inputs:
- pairing_scores_csv (str): path to the CSV file containing historical pairing scores
- attendees_csv (str): path to the CSV file containing attendee information
- weights (List[float]): list containing the weights of gender, year and faculty respectively
- group_size (int): size of each group

Returns:
- groups (List[List[Attendee]]): list of groups, where each group is a list of Attendee objects
'''


def main_workflow(pairing_scores, attendees, weights_list):
    weights = {
        'gender': weights_list[0],
        'year': weights_list[1],
        'faculty': weights_list[2]
    }

    # Retrieve Telegram IDs
    telegram_ids = [attendee.telegram_id for attendee in attendees.values()]
    new_telegram_ids = [id for id in telegram_ids if id not in pairing_scores.index]

    # Add new attendees to pairing scores matrix
    if new_telegram_ids:
        pairing_scores = add_new_attendees(new_telegram_ids, pairing_scores)


    # groups is a list of Group objects
    groups = assign_groups(attendees, pairing_scores, weights)

    # get list of lists of Attendees
    groups_list = [group.members for group in groups]

    # Check goodness of groups
    group_scores = qa.calc_group_quality(groups_list, pairing_scores, weights)
    print(f"Group scores: {group_scores}")

    # Print pairing scores within each group
    qa.print_group_pairings(pairing_scores, groups_list)

    print("Successfully generated groups")
    return groups_list, group_scores


def groups_to_dataframe(groups):
    '''
    Input: groups (List[List[Attendee]]): list of groups, where each group is a list of Attendee objects
    Output: df (pd.DataFrame): DataFrame containing attendees and all attribtes, but now with a 'Group' column
    '''
    data = []

    for idx, group in enumerate(groups, start=1):
        for member in group:
            member_data = vars(member)
            member_data['Group'] = idx
            data.append(member_data)

    df = pd.DataFrame(data)
    df.set_index('name', inplace=True)

    return df
