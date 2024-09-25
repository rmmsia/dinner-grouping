from flask import Flask, render_template, request, jsonify, send_from_directory
from generate import generate
import matrix_patch
import os
import shutil
from datetime import datetime, timedelta
import threading

app = Flask(__name__)

# Ensure the uploads and downloads directories exist
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Dictionary to store file creation times
file_creation_times = {}


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
        threading.Event().wait(120)


# Start the cleanup thread
cleanup_thread = threading.Thread(target=delayed_file_cleanup, daemon=True)
cleanup_thread.start()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'feature1' in request.form:
            csv_file = request.files['csv_file']
            txt_file = request.files['txt_file']
            grp_size = request.form['integer_input']

            # Save the uploaded files
            matrix = os.path.join(UPLOAD_FOLDER, csv_file.filename)
            attendees = os.path.join(UPLOAD_FOLDER, txt_file.filename)
            csv_file.save(matrix)
            txt_file.save(attendees)

            try:
                groups = generate(matrix, attendees, int(grp_size))
                # Create a .txt file with groups in the downloads folder
                output_file = f'groups_{datetime.now().strftime("%Y%m%d%H%M%S")}.txt'
                output_path = os.path.join(DOWNLOAD_FOLDER, output_file)
                with open(output_path, 'w') as f:
                    for idx, group in enumerate(groups, start=1):
                        f.write(f"Group {idx}:\n")
                        for member in group:
                            f.write(f"{member}\n")
                        f.write("\n")
                file_creation_times[output_file] = datetime.now()

                # Clear uploads folder
                clear_upload_folder()

                return jsonify({
                    'groups': groups,
                    'download_url': f'/download/{output_file}'
                })
            except Exception as e:
                print(f"Error: {e}")
                return jsonify({'error': str(e)}), 500

        elif 'feature2' in request.form:
            csv_file = request.files['csv_file2']
            txt_file = request.files['txt_file2']
            patch_value = request.form['patch_score']

            # Save the uploaded files
            csv_path = os.path.join(UPLOAD_FOLDER, csv_file.filename)
            txt_path = os.path.join(UPLOAD_FOLDER, txt_file.filename)
            csv_file.save(csv_path)
            txt_file.save(txt_path)

            try:
                # Process the files and create a DataFrame
                df = matrix_patch.patch_matrix(csv_path, txt_path, patch_value)

                # Save the DataFrame as a CSV file in the downloads folder
                output_file = f'{os.path.basename(csv_path)}_patched.csv'
                output_path = os.path.join(DOWNLOAD_FOLDER, output_file)
                df.to_csv(output_path, index=True)

                file_creation_times[output_file] = datetime.now()

                # Clear uploads folder
                clear_upload_folder()

                return jsonify({
                    'message': 'File processed successfully',
                    'download_url': f'/download/{output_file}'
                })
            except Exception as e:
                print(f"Error: {e}")
                return jsonify({'error': str(e)}), 500

    return render_template('index.html')


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True)
