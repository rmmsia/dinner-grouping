import pandas as pd
import numpy as np
from typing import List, Optional

class GreedyGroupManager:
    # Creates an instance of the GreedyGroupManager class, loading the pairing scores matrix
    def __init__(self, pairing_scores_file: Optional[str] = None):
        if pairing_scores_file:
            self.load_pairing_scores(pairing_scores_file)
        else:
            raise ValueError("Pairing scores matrix must be provided")

    # Loads the pairing scores matrix from a CSV file
    def load_pairing_scores(self, filename: str):
        if filename.endswith('.csv'):
            self.pairing_scores = pd.read_csv(filename, index_col=0)
        else:
            raise ValueError("Unsupported file format. Please use .csv")
        
        self.people = list(self.pairing_scores.index)
        self.pairing_scores = self.pairing_scores.astype(float)
        np.fill_diagonal(self.pairing_scores.values, 0)

    # Creates groups of attendees based on the pairing scores matrix by greedily selecting the best pairings
    def create_groups(self, group_size: int, attendees: List[str]) -> List[List[str]]:
        # Add new attendees to the pairing scores matrix if they don't exist
        new_attendees = [a for a in attendees if a not in self.pairing_scores.index]
        if new_attendees:
            self._add_new_attendees(new_attendees)

        # Filter pairing scores to only include attendees
        available_people = [p for p in attendees if p in self.people]
        filtered_scores = self.pairing_scores.loc[available_people, available_people]

        groups = []

        while len(available_people) >= group_size:
            group = self._form_group_greedy(available_people, group_size, filtered_scores)
            groups.append(group)
            for person in group:
                available_people.remove(person)

        # Handle remaining people
        if available_people:
            for person in available_people:
                group_to_join = min(groups, key=lambda g: filtered_scores.loc[g, person].sum())
                group_to_join.append(person)

        self._update_pairing_scores(groups)
        return groups

    def _add_new_attendees(self, new_attendees: List[str]):
        for attendee in new_attendees:
            self.pairing_scores.loc[attendee] = 0
            self.pairing_scores[attendee] = 0
        self.people.extend(new_attendees)

    # Greedy algorithm to form a group of attendees based on the pairing scores matrix
    def _form_group_greedy(self, available_people: List[str], group_size: int, filtered_scores: pd.DataFrame) -> List[str]:
        first_person = min(available_people, key=lambda p: filtered_scores[p].sum())
        group = [first_person]

        while len(group) < group_size:
            next_person = min(
                [p for p in available_people if p not in group],
                key=lambda p: filtered_scores.loc[group, p].sum()
            )
            group.append(next_person)

        return group

    def _update_pairing_scores(self, groups: List[List[str]]):
        for group in groups:
            for i, person1 in enumerate(group):
                for person2 in group[i+1:]:
                    self.pairing_scores.at[person1, person2] += 1
                    self.pairing_scores.at[person2, person1] += 1

    def save_pairing_scores(self, filename: str):
        # Convert to integers before saving
        integer_scores = self.pairing_scores.astype(int)
        integer_scores.to_csv(filename)

    def print_pairing_scores(self):
        # Print as integers for cleaner output
        print(self.pairing_scores.astype(int))

# User input to pass in pairing scores csv
try:
    pairing_scores_file = input("Enter the pairing scores file ending in '.csv': ")
    if not pairing_scores_file.endswith('.csv'):
        raise ValueError("File must be a csv file")
    with open(pairing_scores_file, 'r') as file:
        if not file.read():
            raise ValueError("File is empty")
except FileNotFoundError:
    raise ValueError("File does not exist")

manager = GreedyGroupManager(pairing_scores_file=pairing_scores_file)

# Pass attendees txt file - get list of attendees for session
try:
    attendees_file = input("Enter the attendees file ending in '.txt': ")
    with open(attendees_file, 'r') as file:
        attendees = [line.strip() for line in file]  # Strip removes newline characters
except FileNotFoundError:
    raise ValueError("File does not exist")

# Set group size
try:
    group_size = int(input("Enter the group size: "))
except ValueError:
    raise ValueError("Group size must be an integer")

# Create groups
print()
groups = manager.create_groups(group_size=group_size, attendees=attendees)
for i, group in enumerate(groups, 1):
    print(f"Group {i}: {group}")
'''
print("\nUpdated Pairing Scores:")
manager.print_pairing_scores()
'''
# Save updated pairing scores
manager.save_pairing_scores("updated_pairing_scores.csv")
print()
print("Pairing scores saved to 'updated_pairing_scores.csv'")