import os
import datetime
import pdb
import uuid
import json
from flask import Flask, request, jsonify

app = Flask(__name__)
UPLOAD_FOLDER = r'C:\Users\mybj2\Desktop\School\Excellenteam\python\final-project-bezJac\uploads'
OUTPUT_FOLDER = r'C:\Users\mybj2\Desktop\School\Excellenteam\python\final-project-bezJac\outputs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        uid = str(uuid.uuid4())

        original_filename = file.filename
        file_name, file_ext = os.path.splitext(original_filename)

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        new_filename = f"{uid}_{timestamp}_{file_name}_{file_ext}"

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))

        return jsonify({'uid': uid})
    else:
        return jsonify({'error': 'No file provided'}), 400


@app.route('/status/<string:uid>', methods=['GET'])
def status(uid):
    #uid = uid[8:]
    uploads_path = app.config['UPLOAD_FOLDER']
    output_path = app.config['OUTPUT_FOLDER']
    file_exists = False
    file_path = None

    for root, dirs, files in os.walk(uploads_path):
        for file in files:
            if uid in file:
                file_exists = True
                file_path = os.path.join(root, file)
                break

    if not file_exists:
        return jsonify({'status': 'not found'}), 404

    filename = os.path.splitext(os.path.basename(file_path))[0]

    timestamp = os.path.basename(file_path).split('_', 1)[1].split('_', 1)[0]
    timestamp = datetime.datetime.strptime(timestamp, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")

    output_filename = f"{filename}.json"
    output_file_path = os.path.join(output_path, output_filename)
    output_exists = os.path.exists(output_file_path)

    response = {
        'status': 'done' if output_exists else 'pending',
        'filename': filename,
        'timestamp': timestamp,
        'explanation': None
    }

    if output_exists:
        with open(output_file_path, 'r') as f:
            output_data = json.load(f)
            response['explanation'] = output_data

    return jsonify(response)


if __name__ == '__main__':
    app.run()