from flask import Flask, render_template, request, jsonify, send_from_directory
from algo_v2 import main_workflow, groups_to_dataframe, Attendee
import pandas as pd
import os
import chardet
import signal
import shutil
import sys
import threading
import webview
from datetime import datetime, timedelta

if hasattr(sys, '_MEIPASS'):
    ROOT_DIR = os.path.join(sys._MEIPASS, 'templates')   # PyInstaller one-file mode
else:
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))   # Dev / py2app mode

app = Flask(__name__, template_folder=ROOT_DIR)

file_creation_times = {}

UPLOAD_FOLDER = os.path.join(ROOT_DIR, 'uploads')
DOWNLOAD_FOLDER = os.path.join(ROOT_DIR, 'downloads')
for folder in [UPLOAD_FOLDER, DOWNLOAD_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)


def clear_upload_folder():
    """Clear all files and directories in the UPLOAD_FOLDER."""
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')


def delayed_file_cleanup():
    """Periodically clean up old files in the DOWNLOAD_FOLDER."""
    while True:
        current_time = datetime.now()
        files_to_delete = []

        for filename, creation_time in file_creation_times.items():
            if current_time - creation_time > timedelta(minutes=2):
                file_path = os.path.join(DOWNLOAD_FOLDER, filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
                files_to_delete.append(filename)

        for filename in files_to_delete:
            del file_creation_times[filename]

        # Run every 2 minutes
        threading.Event().wait(30)


def cleanup(folders_to_clear):
    for folder in folders_to_clear:
        if os.path.exists(folder):
            print(f"Cleaning up folder: {folder}")
            # Delete all files in the folder
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path):  # Check if it's a file
                        os.remove(file_path)  # Remove file
                        print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")


def handle_signal(signal, frame):
    """
    Handle the interrupt signal (Ctrl+C) to clean up before exiting.
    """
    print("\nInterrupted! Performing cleanup...")
    cleanup([UPLOAD_FOLDER, DOWNLOAD_FOLDER])
    sys.exit(0)  # Exit the program after cleanup


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


def close_window():
    """This function is called to close the window and trigger cleanup."""
    print("Closing window and performing cleanup...")
    cleanup([UPLOAD_FOLDER, DOWNLOAD_FOLDER])
    sys.exit(0)


# Start the cleanup thread
cleanup_thread = threading.Thread(target=delayed_file_cleanup, daemon=True)
cleanup_thread.start()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Add debug prints
            print("Form data:", request.form)
            print("Files:", request.files)

            # Check if files are empty using the correct field names
            if 'csv_file' not in request.files or request.files['csv_file'].filename == '':
                return jsonify({'error': 'CSV file is required'}), 400
            if 'attendees_file' not in request.files or request.files['attendees_file'].filename == '':
                return jsonify({'error': 'Attendees file is required'}), 400

            csv_file = request.files['csv_file']
            attendees_file = request.files['attendees_file']  # Updated field name

            # Check for factors
            required_factors = ['factor1', 'factor2', 'factor3']
            if not all(factor in request.form for factor in required_factors):
                return jsonify({'error': 'All weight factors are required'}), 400

            # Get slider values
            try:
                factors = [
                    float(request.form['factor1']),
                    float(request.form['factor2']),
                    float(request.form['factor3'])
                ]
            except ValueError:
                return jsonify({'error': 'Invalid weight factor values'}), 400

            # Validate factors sum to 1.0
            if abs(sum(factors) - 1.0) > 0.01:
                return jsonify({'error': 'Weight factors must sum to 1.0'}), 400

            print("Files and inputs validated successfully")

            # Save uploaded files with unique names to prevent conflicts
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            matrix_filename = f'matrix_{timestamp}_{csv_file.filename}'
            attendees_filename = f'attendees_{timestamp}_{attendees_file.filename}'

            matrix = os.path.join(UPLOAD_FOLDER, matrix_filename)
            attendees = os.path.join(UPLOAD_FOLDER, attendees_filename)

            csv_file.save(matrix)
            attendees_file.save(attendees)

            print("Files saved successfully")

            # Load attendees and pairing scores
            try:
                attendees_data = load_attendees(attendees)
            except ValueError as e:
                return jsonify({'error': f"Invalid attendees file: {str(e)}"}), 400
            except Exception as e:
                return jsonify({'error': f"Error processing attendees file: {str(e)}"}), 500

            try:
                pairing_scores = load_pairing_scores(matrix, attendees_data)
            except Exception as e:
                return jsonify({'error': f"Error processing pairing scores file: {str(e)}"}), 400

            # Generate groups
            try:
                groups, group_scores = main_workflow(pairing_scores, attendees_data, factors)
            except Exception as e:
                return jsonify({'error': f"Error generating groups: {str(e)}"}), 500

            # Create DataFrame with groups for output
            df = groups_to_dataframe(groups)
            output_file = f'groups_{timestamp}.csv'
            output_path = os.path.join(DOWNLOAD_FOLDER, output_file)
            df.to_csv(output_path, index=True)
            file_creation_times[output_file] = datetime.now()

            # Clean up uploaded files (fix)
            for file_path in [matrix, attendees]:
                if os.path.exists(file_path):
                    os.remove(file_path)

            # Convert groups to list of lists of names
            groups = [[member.name for member in group] for group in groups]

            clear_upload_folder()

            if request.form.get('goodness_toggle') != 'true':
                group_scores = None

            return jsonify({
                'groups': groups,
                'goodness_score': group_scores,
                'download_url': f'/download/{output_file}'
            })

        except Exception as e:
            import traceback
            print(f"Error occurred: {str(e)}")
            print(traceback.format_exc())  # Print the full traceback for debugging
            return jsonify({'error': str(e)}), 500

    return render_template('index.html')


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)


def run_flask():
    print("Running Flask app")
    app.run(debug=False)


if __name__ == '__main__':
    # Register the signal handler
    signal.signal(signal.SIGINT, handle_signal)

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Open Flask app in native window
    window = webview.create_window("Group Generator", "http://127.0.0.1:5000")

    window.events.closed += close_window

    webview.start()
