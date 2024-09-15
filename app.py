from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from generate import generate
from grouping import GreedyGroupManager

app = Flask(__name__)

# Ensure the uploads directory exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'feature1' in request.form:
            csv_file = request.files['csv_file']
            txt_file = request.files['txt_file']
            integer_input = request.form['integer_input']
            
            # Save the uploaded files
            csv_filename = os.path.join(UPLOAD_FOLDER, csv_file.filename)
            txt_filename = os.path.join(UPLOAD_FOLDER, txt_file.filename)
            csv_file.save(csv_filename)
            txt_file.save(txt_filename)
            
            # Call the generate function directly
            try:
                groups = generate(csv_filename, txt_filename, int(integer_input))
                
                # Create a .txt file with groups
                txt_filename = os.path.join(UPLOAD_FOLDER, 'groups.txt')
                with open(txt_filename, 'w') as f:
                    for idx, group in enumerate(groups, start=1):
                        f.write(f"Group {idx}:\n")
                        for member in group:
                            f.write(f"{member}\n")
                        f.write("\n")
                
                return jsonify({
                    'groups': groups,
                    'download_url': f'/download/{os.path.basename(txt_filename)}'
                })
            except Exception as e:
                print(f"Error: {e}")
                return jsonify({'error': str(e)}), 500
    
    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
