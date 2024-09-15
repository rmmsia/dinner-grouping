from grouping import GreedyGroupManager

def generate(pairing_scores_file: str, attendees_file: str, group_size: int):

    # Create instance of GreedyGroupManager class
    manager = GreedyGroupManager(pairing_scores_file=pairing_scores_file)

    # Parse attendees
    with open(attendees_file, 'r') as file:
            attendees = [line.strip() for line in file]

    # Create groups
    print()
    groups = manager.create_groups(group_size=group_size, attendees=attendees)
    
    return groups