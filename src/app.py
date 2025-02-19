from flask import Flask, render_template, request, jsonify, send_from_directory
from algo_v2 import main_workflow, groups_to_dataframe
import os
import shutil
import threading
from datetime import datetime, timedelta

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
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

            # Check for group size
            if not request.form.get('integer_input'):
                return jsonify({'error': 'Group size is required'}), 400

            grp_size = request.form['integer_input']

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

            # Generate groups
            groups, group_scores = main_workflow(matrix, attendees, factors, int(grp_size))

            # Create DataFrame with groups for output
            df = groups_to_dataframe(groups)
            output_file = f'groups_{timestamp}.csv'
            output_path = os.path.join(DOWNLOAD_FOLDER, output_file)
            df.to_csv(output_path, index=True)
            file_creation_times[output_file] = datetime.now()

            # Clean up uploaded files
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
            print(f"Error occurred: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return render_template('index.html')


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True)
