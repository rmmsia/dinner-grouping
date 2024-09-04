def pairing_score_file(filename):
    if not filename.endswith('.csv'):
        raise ValueError("File must be a csv file")
    with open(filename, 'r') as file:
        if not file.read():
            raise ValueError("File is empty")

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