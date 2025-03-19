import chardet
import pandas as pd
from algo_v2 import Attendee

def load_attendees(attendees_csv):
    """
    Load attendees from a CSV file.

    Args:
        attendees_csv (str): Path to the CSV file containing attendee information.

    Returns:
        dict: Dictionary mapping attendee names to Attendee objects.

    Raises:
        ValueError: If the CSV file is missing required columns or contains invalid data.
    """
    # Detect encoding of attendees CSV
    with open(attendees_csv, 'rb') as f:
        result = chardet.detect(f.read())
    detected_encoding = result['encoding']

    # Load attendees
    print("Loading attendees")
    try:
        attendees_df = pd.read_csv(attendees_csv, encoding=detected_encoding)

        # Check required columns
        required_columns = ['name', 'gender', 'telegram_id', 'email', 'year', 'faculty']
        missing_columns = [col for col in required_columns if col not in attendees_df.columns]

        if missing_columns:
            error_msg = f"CSV file is missing required columns: {', '.join(missing_columns)}"
            print(error_msg)
            raise ValueError(error_msg)

        # Check if name column has duplicate values
        if attendees_df['name'].duplicated().any():
            duplicate_names = attendees_df[attendees_df['name'].duplicated()]['name'].unique().tolist()
            error_msg = f"CSV file contains duplicate names: {', '.join(duplicate_names)}"
            print(error_msg)
            raise ValueError(error_msg)

        if attendees_df['telegram_id'].duplicated().any():
            duplicate_names = attendees_df[attendees_df['name'].duplicated()]['name'].unique().tolist()
            error_msg = f"CSV file contains duplicate Telegram IDs: {', '.join(duplicate_names)}"
            print(error_msg)
            raise ValueError(error_msg)

        # Check for empty values in critical columns
        for col in ['name', 'telegram_id']:
            if attendees_df[col].isna().any():
                missing_rows = attendees_df[attendees_df[col].isna()].index.tolist()
                error_msg = f"Missing values in '{col}' column at rows: {', '.join(map(str, missing_rows))}"
                print(error_msg)
                raise ValueError(error_msg)

        attendees_df.set_index('name', drop=False, inplace=True)

        attendees = {
            row['name']: Attendee(row['name'], row['gender'], row['telegram_id'], row['email'], row['year'], row['faculty'])
            for _, row in attendees_df.iterrows()
        }
        attendees = {attendee.name: attendee for attendee in attendees.values()}  # key is name, value is Attendee object

        return attendees

    except pd.errors.EmptyDataError:
        error_msg = "The attendees CSV file is empty"
        print(error_msg)
        raise ValueError(error_msg)

    except pd.errors.ParserError as e:
        error_msg = f"Error parsing the attendees CSV file: {str(e)}"
        print(error_msg)
        raise ValueError(error_msg)


def load_pairing_scores(pairing_scores_csv, attendees):
    # Load historical pairing scores
    try:
        pairing_scores = pd.read_csv(pairing_scores_csv, index_col=0)
    except FileNotFoundError:
        attendee_names = list(attendees.keys())
        pairing_scores = pd.DataFrame(0, index=attendee_names, columns=attendee_names)

    return pairing_scores

def parse_groups_txt(filename):
    with open(filename, 'r') as file:
        content = file.read().strip()
    
    # Split content by double lines to get new groups
    groups = content.split('\n\n')

    # Split each group by single lines to get members
    groups = [group.split('\n') for group in groups]

    return groups