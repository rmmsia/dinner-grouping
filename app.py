from flask import Flask, render_template, request, jsonify
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
                return jsonify({'groups': groups})
            except Exception as e:
                print(f"Error: {e}")
                return jsonify({'error': str(e)}), 500
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
