from flask import Flask, render_template, request, jsonify
import os
import subprocess

app = Flask(__name__)

# Ensure the uploads directory exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check which feature was requested
        if 'feature1' in request.form:
            csv_file = request.files['csv_file']
            txt_file = request.files['txt_file']
            integer_input = request.form['integer_input']
            
            # Save the uploaded files
            csv_filename = os.path.join(UPLOAD_FOLDER, csv_file.filename)
            txt_filename = os.path.join(UPLOAD_FOLDER, txt_file.filename)
            csv_file.save(csv_filename)
            txt_file.save(txt_filename)
            
            # Call the external Python script for feature 1
            result = subprocess.run(['python', 'feature1_script.py', csv_filename, txt_filename, integer_input], capture_output=True, text=True)
            
            # Return the output from the script
            return jsonify({'output': result.stdout})
        
        elif 'feature2' in request.form:
            file = request.files['file']
            
            # Save the uploaded file
            filename = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filename)
            
            # Call the external Python script for feature 2
            result = subprocess.run(['python', 'feature2_script.py', filename], capture_output=True, text=True)
            
            # Return the output from the script
            return jsonify({'output': result.stdout})
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)