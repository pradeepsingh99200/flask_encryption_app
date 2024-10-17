from flask import Flask, render_template, request, send_file, redirect, url_for
from cryptography.fernet import Fernet
import os

app = Flask(__name__)

ENCRYPTED_FOLDER = 'encrypted_file'
DECRYPTED_FOLDER = 'decrypted_file'
os.makedirs(ENCRYPTED_FOLDER, exist_ok=True)
os.makedirs(DECRYPTED_FOLDER, exist_ok=True)

def generate_key():
    key = Fernet.generate_key()
    return key

def encrypt_file(file_data, key):
    cipher = Fernet(key)
    encrypted_data = cipher.encrypt(file_data)
    return encrypted_data

def decrypt_file(encrypted_data, key):
    cipher = Fernet(key)
    decrypted_data = cipher.decrypt(encrypted_data)
    return decrypted_data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    
    key = generate_key()
    file_data = file.read()
    
    encrypted_data = encrypt_file(file_data, key)
    
    encrypted_file_path = os.path.join(ENCRYPTED_FOLDER, f"{file.filename}.encrypted")
    
    os.makedirs(os.path.dirname(encrypted_file_path), exist_ok=True)
    
    with open(encrypted_file_path, 'wb') as encrypted_file:
        encrypted_file.write(encrypted_data)
    
    key_str = key.decode('utf-8')
    
    return render_template('download_encrypted.html', 
                           key=key_str, 
                           filename=f"{file.filename}.encrypted")

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(ENCRYPTED_FOLDER, filename)
    return send_file(file_path, as_attachment=True)

@app.route('/decrypt', methods=['POST'])
def decrypt():
    if 'file' not in request.files or 'key' not in request.form:
        return "Missing file or key"
    
    file = request.files['file']
    key_str = request.form['key']
    
    if file.filename == '':
        return "No selected file"
    
    key = key_str.encode('utf-8')
    encrypted_data = file.read()
    
    try:
        decrypted_data = decrypt_file(encrypted_data, key)
    except Exception as e:
        return f"Invalid key or corrupted file: {str(e)}"
    
    decrypted_file_path = os.path.join(DECRYPTED_FOLDER, file.filename.replace('.encrypted', ''))
    
    os.makedirs(os.path.dirname(decrypted_file_path), exist_ok=True)
    
    with open(decrypted_file_path, 'wb') as decrypted_file:
        decrypted_file.write(decrypted_data)
    
    return send_file(decrypted_file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)