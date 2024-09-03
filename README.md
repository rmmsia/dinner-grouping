# Dinner Grouping

## Installation

**Prerequisites**

- Python 3.12.4 or higher
- Anaconda installation (if installing environment with `grouping-env.yml`)
- `.csv` file containing a Pairing Score Matrix
- `.txt` file containing the names of attendees that you want to put into groups

**Run**

- ***Pip***
  - Install the required libraries: `pip install -r requirements.txt`
- ***Anaconda***:
  - Create the environment: `conda env create -f group-env.yml`
  - Activate the new environment: `conda activate dinner-group`
- Run the program with `python main.py`

**Note:** Ensure that when prompted, you include the file extension as well (e.g. `.csv` or `.txt`), otherwise the program will reject the input. Sample data has been provided (`sample.csv`)

## Description

This is a greedy algorithm that uses a 'pairing score' system to choose members from a list of attendees based on how low their pairing scores with every other member in the group are.

A **pairing score** of two people is the number of times these two people have been in the same group together in the past. For example, if Alice and Bob have been assigned to the same dinner group for five previous sessions, then their pairing score would be 5.

Members are iteratively added to groups, where at each step, the person that has the lowest total pairing score with everyone already inside the group is added.

While the algorithm is not perfect, it works well enough for the purposes of minimising repeat groupings.