import pandas as pd
import numpy as np
from typing import List, Optional


class GreedyGroupManager:
    # Initialise group matrix
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

    # Creates groups of attendees by greedily selecting the best pairings
    def create_groups(self, group_size: int, attendees: List[str]) -> List[List[str]]:
        # Add new attendees to the pairing scores matrix if they don't exist
        new_attendees = [a for a in attendees if a not in self.pairing_scores.index]
        if new_attendees:
            self._add_new_attendees(new_attendees)

        # Filter pairing scores to only include attendees
        available_people = [p for p in attendees if p in self.people]
        filtered_scores = self.pairing_scores.loc[available_people, available_people]

        groups = []
        num_full_groups = len(available_people) // group_size

        # Form full-sized groups
        for _ in range(num_full_groups):
            group = self._form_group_greedy(available_people, group_size, filtered_scores)
            groups.append(group)

        # Handle the remaining people (if any)
        if available_people:
            groups.append(available_people)

        # self._update_pairing_scores(groups)
        return groups

    def _add_new_attendees(self, new_attendees: List[str]):
        for attendee in new_attendees:
            self.pairing_scores.loc[attendee] = 0
            self.pairing_scores[attendee] = 0
        self.people.extend(new_attendees)

    # Greedy algorithm to form a group of attendees based on the pairing scores matrix
    def _form_group_greedy(self, available_people: List[str], group_size: int, filtered_scores: pd.DataFrame) -> List[str]:
        group = []

        while len(group) < group_size:
            best_person = None
            best_score = float('inf')

            for person in available_people:
                if person in group:
                    continue

                # Check if adding this person violates any constraints
                if any(filtered_scores.loc[other_person, person] == 99 for other_person in group):
                    continue

                # Calculate the total score if this person is added to the group
                score = filtered_scores.loc[group, person].sum()

                if score < best_score:
                    best_score = score
                    best_person = person

            if best_person is None:
                break

            # Ensure best_person is in available_people before removal
            if best_person in available_people:
                group.append(best_person)
                available_people.remove(best_person)

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
