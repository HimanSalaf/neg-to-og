from flask import Flask, render_template, request, redirect, url_for
import cv2
import numpy as np
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def invert_negative(image_path, output_path):
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        return None

    if len(img.shape) == 3 and img.shape[-1] == 4:  # RGBA
        inverted_img = img.copy()
        inverted_img[..., :3] = 255 - img[..., :3]  # Invert RGB
        inverted_img[..., 3] = img[..., 3]          # Preserve Alpha
    elif len(img.shape) in [2, 3]:  # Grayscale or RGB
        inverted_img = 255 - img
    else:
        return None

    cv2.imwrite(output_path, inverted_img)
    return output_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        return "Invalid file type", 400

    # Create unique filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    original_filename = secure_filename(file.filename)
    filename = f"{timestamp}_{original_filename}"
    
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(upload_path)

    result_filename = f"inverted_{filename}"
    result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)
    inverted_image_path = invert_negative(upload_path, result_path)

    if inverted_image_path is None:
        return "Processing error or invalid image format", 500

    return render_template(
        'result.html',
        original_image=f'uploads/{filename}',
        processed_image=f'results/{result_filename}'
    )

if __name__ == '__main__':
    app.run(debug=True)
