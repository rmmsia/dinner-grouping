from datetime import datetime
from grouping import GreedyGroupManager
import file_input_util as fiu

def generate():
    # User input to pass in pairing scores csv
    pairing_scores_file = fiu.pairing_score_file()

    # Create instance of GreedyGroupManager class
    manager = GreedyGroupManager(pairing_scores_file=pairing_scores_file)

    # Pass attendees txt file - get list of attendees for session
    attendees = fiu.attendees_file()

    # Set group size
    group_size = int(input("Enter the group size: "))

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