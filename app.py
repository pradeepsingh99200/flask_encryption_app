from flask import Flask, render_template, request, send_file, redirect, url_for
from cryptography.fernet import Fernet
import os

app = Flask(__name__)

# Function to generate and save the encryption key
def generate_key():
    key = Fernet.generate_key()
    return key

# Function to encrypt the file
def encrypt_file(file_data, key):
    cipher = Fernet(key)
    encrypted_data = cipher.encrypt(file_data)
    return encrypted_data

# Function to decrypt the file
def decrypt_file(encrypted_data, key):
    cipher = Fernet(key)
    decrypted_data = cipher.decrypt(encrypted_data)
    return decrypted_data

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle file encryption
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
    
    # Save the encrypted file temporarily
    encrypted_file_path = os.path.join('encrypted_file', f"{file.filename}.encrypted")
    with open(encrypted_file_path, 'wb') as encrypted_file:
        encrypted_file.write(encrypted_data)
    
    # Convert the key to string for display
    key_str = key.decode('utf-8')
    
    # Return the download link for the encrypted file and show the key
    return render_template('download_encrypted.html', 
                           key=key_str, 
                           filename=f"{file.filename}.encrypted")

# Route to download the encrypted file
@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join('encrypted_file', filename)
    return send_file(file_path, as_attachment=True)

# Route to handle file decryption
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
    
    # Save the decrypted file temporarily
    decrypted_file_path = os.path.join('decrypted_file', file.filename.replace('.encrypted', ''))
    with open(decrypted_file_path, 'wb') as decrypted_file:
        decrypted_file.write(decrypted_data)
    
    # Return the download link for the decrypted file
    return send_file(decrypted_file_path, as_attachment=True)

if __name__ == '__main__':
    # # Create directories if not exist
    # os.makedirs('encrypted_file', exist_ok=True)
    # os.makedirs('decrypted_file', exist_ok=True)
    
    app.run(debug=True)
