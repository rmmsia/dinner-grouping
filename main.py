from datetime import datetime
from grouping import GreedyGroupManager

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

# Create instance of GreedyGroupManager class
manager = GreedyGroupManager(pairing_scores_file=pairing_scores_file)

# Pass attendees txt file - get list of attendees for session
try:
    attendees_file = input("Enter the attendees file ending in '.txt': ")
    with open(attendees_file, 'r') as file:
        attendees = [line.strip() for line in file]  # Separates each line into a list item
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

# Save updated pairing scores
timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
manager.save_pairing_scores(f"pairing_scores_{timestamp}.csv")
print()
print(f"Pairing scores saved to 'pairing_scores_{timestamp}.csv'")