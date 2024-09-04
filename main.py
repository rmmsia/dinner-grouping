from grouping import GreedyGroupManager
from generate import generate
import file_input_util as fiu
from datetime import datetime
# User input. Enter 1 to Generate groups or 2 to update pairing scores.

user_input = int(input("Enter 1 to Generate groups or 2 to update pairing scores: "))
if user_input == 1:
    generate()

elif user_input == 2:
    pairing_scores_file = fiu.pairing_score_file()

    manager = GreedyGroupManager(pairing_scores_file=pairing_scores_file)

    grouping_file = fiu.grouping_file()

    # Update pairing scores
    manager.update_pairing_scores(grouping_file)

    # Save updated pairing scores
    timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    manager.save_pairing_scores(f"pairing_scores_{timestamp}.csv")
    print()
    print(f"Pairing scores saved to 'pairing_scores_{timestamp}.csv'")