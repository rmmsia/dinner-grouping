from collections import defaultdict


def calc_group_quality(groups, matrix, weights):
    group_scores = []  # To store the goodness score for each group

    # Initialize counters for group proportions
    for group in groups:
        year_count = defaultdict(int)
        faculty_count = defaultdict(int)
        gender_count = defaultdict(int)

        total_diversity_score = 0
        total_repeat_pairings = 0
        total_possible_pairs = 0
        group_size = len(group)

        # Update the counts for year, faculty, and gender
        for attendee in group:
            year_count[attendee.year] += 1
            faculty_count[attendee.faculty] += 1
            gender_count[attendee.gender] += 1

        # Track pairings for repeat grouping
        for i, attendee1 in enumerate(group):
            for attendee2 in group[i + 1:]:
                repeat_count = matrix.at[attendee1.telegram_id, attendee2.telegram_id]
                total_repeat_pairings += repeat_count  # Linear punishment repeats based on score
                total_possible_pairs += 1

        # Compute diversity score based on proportions and weights
        expected_year = weights['year'] * group_size
        expected_faculty = weights['faculty'] * group_size
        expected_gender = weights['gender'] * group_size

        diversity_score = (abs(year_count[attendee.year] - expected_year)
                           + abs(faculty_count[attendee.faculty] - expected_faculty)
                           + abs(gender_count[attendee.gender] - expected_gender))
        total_diversity_score += diversity_score

        # Normalize the diversity score by the group size
        normalized_diversity_score = total_diversity_score / group_size

        # Normalize the repeat pairing score
        normalized_repeat_pairing_score = total_repeat_pairings / total_possible_pairs if total_possible_pairs > 0 else 0

        # Combine the two scores into a final group-specific goodness score
        group_goodness_score = (normalized_diversity_score + (1 - normalized_repeat_pairing_score))
        group_scores.append(group_goodness_score)

    return group_scores


def print_group_pairings(matrix, groups):
    for group_idx, group in enumerate(groups):
        print(f"Group {group_idx + 1}:")
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                attendee1 = group[i]
                attendee2 = group[j]
                score = matrix.at[attendee1.telegram_id, attendee2.telegram_id]
                print(f"  {attendee1.telegram_id} - {attendee2.telegram_id}: {score}")
