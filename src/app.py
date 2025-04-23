from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from algo_v2 import main_workflow, groups_to_dataframe, generate_default_psm
from loaders import load_attendees, load_pairing_scores
from patcher import patch_matrix, parse_groups_csv
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
            # PSM file is now optional
            if 'attendees_file' not in request.files or request.files['attendees_file'].filename == '':
                return jsonify({'error': 'Attendees file is required'}), 400

            # PSM file is optional
            psm_file = None
            if 'psm_file' in request.files and request.files['psm_file'].filename != '':
                psm_file = request.files['psm_file']

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
            attendees_filename = f'attendees_{timestamp}_{attendees_file.filename}'
            attendees = os.path.join(UPLOAD_FOLDER, attendees_filename)
            attendees_file.save(attendees)

            # Handle optional PSM file
            matrix = None
            if psm_file:
                matrix_filename = f'matrix_{timestamp}_{psm_file.filename}'
                matrix = os.path.join(UPLOAD_FOLDER, matrix_filename)
                psm_file.save(matrix)

            print("Files saved successfully")

            # Load attendees and pairing scores
            try:
                attendees_data = load_attendees(attendees)
            except ValueError as e:
                return jsonify({'error': f"Invalid attendees file: {str(e)}"}), 400
            except Exception as e:
                return jsonify({'error': f"Error processing attendees file: {str(e)}"}), 500

            # Handle optional PSM file
            if matrix:
                try:
                    pairing_scores = load_pairing_scores(matrix)
                except Exception as e:
                    return jsonify({'error': f"Error processing pairing scores file: {str(e)}"}), 400
            else:
                # Create default pairing scores if no PSM file provided
                # This assumes main_workflow can handle None or a default matrix
                pairing_scores = generate_default_psm(attendees_data)

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
            if matrix:
                if os.path.exists(matrix):
                    os.remove(matrix)
            if os.path.exists(attendees):
                os.remove(attendees)

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


@app.route('/patch', methods=['POST'])
def patch_data():
    try:
        # Check if files are empty
        if 'pairing_scores_file' not in request.files or request.files['pairing_scores_file'].filename == '':
            return jsonify({'error': 'Pairing scores CSV file is required'}), 400
        if 'previous_groups_file' not in request.files or request.files['previous_groups_file'].filename == '':
            return jsonify({'error': 'Previous groups CSV file is required'}), 400

        # Get the patch value from form
        try:
            patch_value = int(request.form.get('patch_value', 1))
            if patch_value <= 0:
                return jsonify({'error': 'Patch value must be a positive integer'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid patch value'}), 400

        pairing_scores_file = request.files['pairing_scores_file']
        previous_groups_file = request.files['previous_groups_file']

        # Save uploaded files with unique names
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        scores_filename = f'scores_{timestamp}_{pairing_scores_file.filename}'
        groups_filename = f'groups_{timestamp}_{previous_groups_file.filename}'

        scores_path = os.path.join(UPLOAD_FOLDER, scores_filename)
        groups_path = os.path.join(UPLOAD_FOLDER, groups_filename)

        pairing_scores_file.save(scores_path)
        previous_groups_file.save(groups_path)

        print("Files saved successfully for patching")

        try:
            # Load the pairing scores matrix
            pairing_scores = load_pairing_scores(scores_path)

            groups = parse_groups_csv(groups_path)
            
            # Update the dataframe using the patcher function
            updated_df = patch_matrix(pairing_scores, groups, patch_value)
            print("Pairing scores patched successfully")
            
            # Save the updated dataframe
            output_file = f'patched_scores_{timestamp}.csv'
            output_path = os.path.join(DOWNLOAD_FOLDER, output_file)
            updated_df.to_csv(output_path)
            file_creation_times[output_file] = datetime.now()

            # Clean up uploaded files
            for file_path in [scores_path, groups_path]:
                if os.path.exists(file_path):
                    os.remove(file_path)

            # Return response in the SAME format as the index route
            return jsonify({
                'success': True,
                'message': 'Pairing scores matrix updated successfully',
                'download_url': f'/download/{output_file}'
            })

        except Exception as e:
            import traceback
            print(f"Error patching pairing scores: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'error': f"Error patching pairing scores: {str(e)}"}), 500

    except Exception as e:
        import traceback
        print(f"Error occurred: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@app.route('/download/<filename>')
def download_file(filename):
    """Serve a file from the download directory as an attachment."""
    # Security check to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return "Invalid filename", 400
        
    return send_file(
        os.path.join(DOWNLOAD_FOLDER, filename),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


def run_flask():
    print("Running Flask app")
    app.run(debug=False)


if __name__ == '__main__':
    # Register the signal handler
    signal.signal(signal.SIGINT, handle_signal)
    
    # Simple vanilla Flask server
    print("Running Flask app at http://127.0.0.1:5000")
    print("Press Ctrl+C to exit")
    
    # Enable debug mode for auto-reloading when code changes
    app.run(debug=True)
