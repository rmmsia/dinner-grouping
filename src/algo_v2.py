import random
import pandas as pd
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


def assign_groups(attendees, group_size, matrix, weights):
    print(weights)
    groups = []
    ungrouped = list(attendees.values())
    random.shuffle(ungrouped)

    while ungrouped:
        group = []

        while len(group) < group_size and ungrouped:
            best_candidate = None
            best_score = float('-inf')

            for candidate in ungrouped:
                # Calculate diversity score
                diversity_score = calc_diversity_score(candidate, group, weights)

                # Calculate repetition penalty
                # TODO: Use email in future as that is immutable, for now use telegram_id
                repeat_penalty = sum(
                    matrix.loc[candidate.telegram_id, member.telegram_id] for member in group
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
                group.append(best_candidate)
                ungrouped.remove(best_candidate)

        groups.append(group)

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


'''
Main workflow takes in the following inputs:
- pairing_scores_csv (str): path to the CSV file containing historical pairing scores
- attendees_csv (str): path to the CSV file containing attendee information
- weights (List[float]): list containing the weights of gender, year and faculty respectively
- group_size (int): size of each group

Returns:
- groups (List[List[Attendee]]): list of groups, where each group is a list of Attendee objects
'''


def main_workflow(pairing_scores_csv, attendees_csv, weights_list, group_size):
    # Load attendees
    print("Loading attendees")
    attendees_df = pd.read_csv(attendees_csv)
    attendees_df.set_index('Name', drop=False, inplace=True)

    attendees = {
        row['Name']: Attendee(row['Name'], row['Gender'], row['Telegram ID'], row['Email'], row['Year'], row['Faculty'])
        for _, row in attendees_df.iterrows()
    }
    attendees = {attendee.name: attendee for attendee in attendees.values()}  # key is name, value is Attendee object

    # Load historical pairing scores
    try:
        pairing_scores = load_pairing_score_matrix(pairing_scores_csv)
    except FileNotFoundError:
        attendee_names = list(attendees.keys())
        pairing_scores = pd.DataFrame(0, index=attendee_names, columns=attendee_names)

    weights = {
        'gender': weights_list[0],
        'year': weights_list[1],
        'faculty': weights_list[2]
    }

    groups = assign_groups(attendees, group_size, pairing_scores, weights)

    print("Successfully generated groups")
    return groups


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
