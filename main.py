import pandas as pd
import numpy as np
from typing import List, Optional

class GreedyGroupManager:
    def __init__(self, pairing_scores_file: Optional[str] = None, people: Optional[List[str]] = None):
        if pairing_scores_file:
            self.load_pairing_scores(pairing_scores_file)
        elif people:
            self.people = people
            self.pairing_scores = pd.DataFrame(0, index=people, columns=people)
            np.fill_diagonal(self.pairing_scores.values, 0)
        else:
            raise ValueError("Either pairing_scores_file or people must be provided")

    def load_pairing_scores(self, filename: str):
        if filename.endswith('.csv'):
            self.pairing_scores = pd.read_csv(filename, index_col=0)
        elif filename.endswith(('.xls', '.xlsx')):
            self.pairing_scores = pd.read_excel(filename, index_col=0)
        else:
            raise ValueError("Unsupported file format. Please use .csv, .xls, or .xlsx")
        
        self.people = list(self.pairing_scores.index)
        self.pairing_scores = self.pairing_scores.astype(float)
        np.fill_diagonal(self.pairing_scores.values, 0)

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

# Example usage
manager = GreedyGroupManager(pairing_scores_file="FIDES Cumulative Dinner Attendance AY2425 Sem 1.csv")

# List of attendees for this session, including a new person
attendees = ["velociryan", "qkobs", "adriechue", "luketaneh", "mrjiahao", "etheIyn", "kkchris", "Swirlyz", "joan_aw", "new_person"]

# Create groups
groups = manager.create_groups(group_size=3, attendees=attendees)
for i, group in enumerate(groups, 1):
    print(f"Group {i}: {group}")

print("\nUpdated Pairing Scores:")
manager.print_pairing_scores()

# Save updated pairing scores
manager.save_pairing_scores("updated_pairing_scores.csv")