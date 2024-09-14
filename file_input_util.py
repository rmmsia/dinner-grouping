import csv

def pairing_score_file():
    filename = input("Enter the pairing scores file ending in '.csv': ")
    if not filename.endswith('.csv'):
        raise ValueError("File must be a csv file")
    with open(filename, 'r') as file:
        if not file.read():
            raise ValueError("File is empty")
    return filename

def attendees_file():
    try:
        attendees_file = input("Enter the attendees file ending in '.txt': ")
        with open(attendees_file, 'r') as file:
            attendees = [line.strip() for line in file]  # Separates each line into a list item
            if not attendees:
                raise ValueError("File is empty")
            return attendees
    except FileNotFoundError:
        raise ValueError("File does not exist")
    
def grouping_file():
    grouping_file = input("Enter the grouping file ending in '.csv': ")
    if not grouping_file.endswith('.csv'):
        raise ValueError("File must be a csv file")

    # Initialize an empty list to store the rows
    list_of_lists = []

    # Open the file and parse it
    with open(grouping_file, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            list_of_lists.append(row)