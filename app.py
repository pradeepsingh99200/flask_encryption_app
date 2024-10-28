from flask import Flask, render_template, request, send_file, redirect, url_for , session , flash , jsonify
from cryptography.fernet import Fernet
import os , requests 
from models import create_user, check_user

from datetime import datetime
from database import get_db_connection


app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

API_URL = "https://bdeliver.net/simplelogin" 


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
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'type' in session:
         return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Assume this is your user authentication logic
        response = requests.post(API_URL, json={"email": email, "password": password})
        
        if response.status_code == 200:
            user_info = response.json()
            session['user_id'] = user_info['user']['id']     
            session['username'] = user_info['user']['name']  # Store the user's name in session
            session['type'] = user_info['user']['type']

            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        
        else:
            flash('Invalid email or password. Please try again.', 'error')
    return render_template('login.html')



@app.route('/proxy/getuserdata/<int:company_id>', methods=['GET'])
def proxy_get_userdata(company_id):
    response = requests.get(f"https://bdeliver.net/getuserdata/{company_id}")
    
    if response.status_code == 200:
        # Assuming the API returns a JSON array of users
        return jsonify(response.json())  # Return the JSON response to the client
    else:
        return jsonify({"error": "Failed to fetch user data"}), response.status_code


@app.route('/encrypt', methods=['POST'])
def encrypt():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file"

    # Generate the encryption key and encrypt the file
    key = generate_key()
    file_data = file.read()
    encrypted_data = encrypt_file(file_data, key)

    # Save the encrypted file
    encrypted_file_path = os.path.join(ENCRYPTED_FOLDER, f"{file.filename}.encrypted")
    os.makedirs(os.path.dirname(encrypted_file_path), exist_ok=True)
    
    with open(encrypted_file_path, 'wb') as encrypted_file:
        encrypted_file.write(encrypted_data)

    # Get user info from the session
    user_id = session['user_id']  # Assuming this is set at login
    receiver_id = request.form.get('receiver_id')  # Get the selected user ID from the form
    key_str = key.decode('utf-8')

    # Store details in the database
    conn = get_db_connection()
    cursor = conn.cursor() 
    cursor.execute("""
        INSERT INTO upload (filename, user_id, privatekey, created_at, receiver_id,receiver_emailid)
        VALUES (%s, %s, %s, %s, %s,%s)
    """, (file.filename, user_id, key_str, datetime.now(), receiver_id,request.form.get('email_id')))
    conn.commit()
    cursor.close()
    conn.close()

    return render_template('download_encrypted.html', key=key_str, filename=f"{file.filename}.encrypted")

@app.route('/logout')
def logout():
    session.pop('user_id', None)  
    session.clear()  
    return redirect(url_for('login'))  

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(ENCRYPTED_FOLDER, filename)
    return send_file(file_path, as_attachment=True)

@app.route('/dashboard')
def dashboard():
            if 'type' in session:
                 # Fetch the company list after successful login
                company_response = requests.get("https://bdeliver.net/getcomplist/")
                if company_response.status_code == 200:
                    try:
                        companies = company_response.json()
                    except ValueError as e:
                        print(f"JSON decoding failed: {e}")
                        companies = []
                else:
                    print(f"Failed to fetch company list: {company_response.status_code}, {company_response.text}")
                    companies = []

                # Database query to retrieve user's upload records
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                                        # Determine the condition based on user type
                        user_id = session.get('user_id')
                        user_type = session['type']

                        # Construct the query dynamically
                        query = """
                            SELECT *
                            FROM upload
                            """ + ("WHERE user_id = %s" if user_type == 2 else "WHERE receiver_id = %s")

                        # Set the parameter to be used in the WHERE clause
                        param = (user_id,)

                        # Execute the query
                        cursor.execute(query, param)
                        user_uploads = cursor.fetchall()

                except Exception as e:
                    print(f"Database query failed: {e}")
                    user_uploads = []
                finally:
                    cursor.close()
                    conn.close()

                # Render different templates based on user type, and pass the upload data if applicable
                if session['type'] == 2:
                    return render_template('index.html', companies=companies, username=session['username'], uploads=user_uploads)
                elif session['type'] == 3:
                    return render_template('index2.html', username=session['username'], uploads=user_uploads)
            else:
                return redirect(url_for('login'))
    
           

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
    
    # Get receiver_id from form input (you need to add this to your HTML form)
    receiver_id = request.form.get('userEmails')  # Assuming you are passing this value
    
    # Store download details in the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO download (filename, receiver_id, created_at)
        VALUES (%s, %s, %s)
    """, (file.filename.replace('.encrypted', ''), session['user_id'], datetime.now()))
    conn.commit()
    cursor.close()
    conn.close()
    
    return send_file(decrypted_file_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)