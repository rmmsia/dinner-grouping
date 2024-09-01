import pandas as pd
import numpy as np
from typing import List, Optional

class GreedyGroupManager:
    def __init__(self, pairing_scores_file: Optional[str] = None, people: Optional[List[str]] = None):
        if pairing_scores_file:
            # Load existing pairing scores
            self.load_pairing_scores(pairing_scores_file)
            # Backup the original pairing scores to update later
        elif people:
            self.people = people
            self.pairing_scores = pd.DataFrame(0, index=people, columns=people)
            np.fill_diagonal(self.pairing_scores.values, 0)
        else:
            raise ValueError("Either pairing_scores_file or people must be provided")

    def load_pairing_scores(self, filename: str):
        # Detect file type and read accordingly
        # if filename.endswith('.csv'):
        #    self.pairing_scores = pd.read_csv(filename, index_col=0)
        if filename.endswith(('.xls', '.xlsx')):
            self.pairing_scores = pd.read_excel(filename, index_col=0)
        else:
            raise ValueError("Unsupported file format. Please use .csv, .xls, or .xlsx")
        
        self.people = list(self.pairing_scores.index)
        np.fill_diagonal(self.pairing_scores.values, np.nan)

    def create_groups(self, group_size: int) -> List[List[str]]:
        available_people = self.people.copy()
        groups = []

        while len(available_people) >= group_size:
            group = self._form_group_greedy(available_people, group_size)
            groups.append(group)
            for person in group:
                available_people.remove(person)

        # Handle remaining people
        if available_people:
            for person in available_people:
                group_to_join = min(groups, key=lambda g: self.pairing_scores.loc[g, person].sum())
                group_to_join.append(person)

        self._update_pairing_scores(groups)
        return groups

    def _form_group_greedy(self, available_people: List[str], group_size: int) -> List[str]:
        # Start with the person with the lowest total pairing score
        first_person = min(available_people, key=lambda p: self.pairing_scores[p].sum())
        group = [first_person]

        while len(group) < group_size:
            next_person = min(
                [p for p in available_people if p not in group],
                key=lambda p: self.pairing_scores.loc[group, p].sum()
            )
            group.append(next_person)

        return group

    def _update_pairing_scores(self, groups: List[List[str]]):
        for group in groups:
            for person1 in group:
                for person2 in group:
                    if person1 != person2:
                        self.pairing_scores.at[person1, person2] += 1
                        self.pairing_scores.at[person2, person1] += 1

    def save_pairing_scores(self, filename: str):
        self.pairing_scores.to_csv(filename)

    def load_pairing_scores(self, filename: str):
        self.pairing_scores = pd.read_csv(filename, index_col=0)
        self.people = list(self.pairing_scores.index)

    def print_pairing_scores(self):
        print(self.pairing_scores)

# Example usage
# With existing pairing scores
manager = GreedyGroupManager(pairing_scores_file="FIDES Cumulative Dinner Attendance AY2425 Sem 1.csv")
'''
# Without existing pairing scores
people = ["Alice", "Bob", "Charlie", "David", "Eve"]
manager = GreedyGroupManager(people=people)
'''
# Create groups
groups = manager.create_groups(group_size=7)
for i, group in enumerate(groups, 1):
    print(f"Group {i}: {group}")

print("\nUpdated Pairing Scores:")
manager.print_pairing_scores()

# Save updated pairing scores
manager.save_pairing_scores("updated_pairing_scores.csv")