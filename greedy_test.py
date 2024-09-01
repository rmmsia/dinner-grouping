import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, mock_open
from io import StringIO
from main import GreedyGroupManager  # Adjust the import as necessary

class TestGreedyGroupManager(unittest.TestCase):
    def setUp(self):
        # Set up a simple pairing scores DataFrame for testing
        data = {
            'Alice': [0, 1, 2, 3],
            'Bob': [1, 0, 1, 4],
            'Charlie': [2, 1, 0, 1],
            'David': [3, 4, 1, 0]
        }
        self.pairing_scores_df = pd.DataFrame(data, index=['Alice', 'Bob', 'Charlie', 'David'])
        self.pairing_scores_csv = self.pairing_scores_df.to_csv()

    def test_init_with_valid_pairing_scores_file(self):
        with patch('builtins.open', mock_open(read_data=self.pairing_scores_csv)), \
             patch('pandas.read_csv', return_value=self.pairing_scores_df):
            manager = GreedyGroupManager(pairing_scores_file="scores.csv")
            self.assertEqual(manager.people, ['Alice', 'Bob', 'Charlie', 'David'])
            np.testing.assert_array_equal(manager.pairing_scores.values, self.pairing_scores_df.values)

    def test_init_with_invalid_file_extension(self):
        with self.assertRaises(ValueError) as context:
            GreedyGroupManager(pairing_scores_file="scores.txt")
        self.assertEqual(str(context.exception), "Unsupported file format. Please use .csv, .xls, or .xlsx")

    def test_set_attendees_with_valid_attendees(self):
        with patch('builtins.open', mock_open(read_data=self.pairing_scores_csv)), \
             patch('pandas.read_csv', return_value=self.pairing_scores_df):
            manager = GreedyGroupManager(pairing_scores_file="scores.csv")
            manager.set_attendees(['Alice', 'Bob'])
            self.assertEqual(manager.attendees, ['Alice', 'Bob'])
            np.testing.assert_array_equal(manager.pairing_scores.values, self.pairing_scores_df.loc[['Alice', 'Bob'], ['Alice', 'Bob']].values)

    def test_set_attendees_with_invalid_attendees(self):
        with patch('builtins.open', mock_open(read_data=self.pairing_scores_csv)), \
             patch('pandas.read_csv', return_value=self.pairing_scores_df):
            manager = GreedyGroupManager(pairing_scores_file="scores.csv")
            with self.assertRaises(ValueError) as context:
                manager.set_attendees(['Alice', 'Eve'])
            self.assertEqual(str(context.exception), "Invalid attendees provided: Eve")

    def test_create_groups(self):
        with patch('builtins.open', mock_open(read_data=self.pairing_scores_csv)), \
             patch('pandas.read_csv', return_value=self.pairing_scores_df):
            manager = GreedyGroupManager(pairing_scores_file="scores.csv")
            manager.set_attendees(['Alice', 'Bob', 'Charlie', 'David'])
            groups = manager.create_groups(2)
            self.assertEqual(len(groups), 2)
            self.assertTrue(all(len(group) == 2 for group in groups))

    def test_create_groups_with_odd_number_of_attendees(self):
        with patch('builtins.open', mock_open(read_data=self.pairing_scores_csv)), \
             patch('pandas.read_csv', return_value=self.pairing_scores_df):
            manager = GreedyGroupManager(pairing_scores_file="scores.csv")
            manager.set_attendees(['Alice', 'Bob', 'Charlie'])
            groups = manager.create_groups(2)
            self.assertEqual(len(groups), 2)
            self.assertEqual(len(groups[0]), 2)
            self.assertEqual(len(groups[1]), 1)

    def test_save_pairing_scores(self):
        with patch('builtins.open', mock_open()), \
             patch('pandas.DataFrame.to_csv') as mock_to_csv:
            manager = GreedyGroupManager(pairing_scores_file="scores.csv")
            manager.save_pairing_scores("output.csv")
            mock_to_csv.assert_called_once_with("output.csv")

    def test_print_pairing_scores(self):
        with patch('builtins.open', mock_open(read_data=self.pairing_scores_csv)), \
             patch('pandas.read_csv', return_value=self.pairing_scores_df), \
             patch('builtins.print') as mock_print:
            manager = GreedyGroupManager(pairing_scores_file="scores.csv")
            manager.print_pairing_scores()
            mock_print.assert_called_once_with(manager.original_pairing_scores)

if __name__ == '__main__':
    unittest.main()
