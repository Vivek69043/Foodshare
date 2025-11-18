import os
import json
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session
)

UPLOAD_FOLDER = 'static/uploads'
DB_FILE = 'data.json'
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = 'super-secret-key'  
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------ USERS FOR LOGIN ---------------------
users = {
    "donor": {"username": "donor", "password": "123"},
    "ngo": {"username": "ngo", "password": "123"}
}
# ---------------------------------------------------------

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump([], f)
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ================= HOME PAGE ==========================
@app.route('/')
def index():
    return render_template('index.html')

# ================= LOGIN SYSTEM =======================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')

        if role in users and username == users[role]["username"] and password == users[role]["password"]:
            session['role'] = role
            flash("Login successful!", "success")

            if role == "donor":
                return redirect(url_for('donor'))
            else:
                return redirect(url_for('ngo'))

        flash("Invalid username or password", "danger")

    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('role', None)
    flash("Logged out successfully!", "info")
    return redirect(url_for('login'))

# ================= DONOR PAGE =========================
@app.route('/donor', methods=['GET', 'POST'])
def donor():

    # ACCESS PROTECTION
    if session.get('role') != 'donor':
        flash("Please login as Donor first!", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':

        food_type   = request.form.get('food_type', 'Other')
        dish_name   = request.form.get('dish_name', '')
        quantity    = request.form.get('quantity', 'Unknown')
        location    = request.form.get('location', 'Unknown')
        pickup_time = request.form.get('pickup_time', 'ASAP')
        notes       = request.form.get('notes', '')

        file = request.files.get('image')
        filename = ''

        if file and allowed_file(file.filename):
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{timestamp}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_post = {
            "id": int(datetime.now().timestamp() * 1000),
            "image": filename,
            "food_type": food_type,
            "dish_name": dish_name,
            "quantity": quantity,
            "location": location,
            "pickup_time": pickup_time,
            "notes": notes,
            "status": "Available",
            "claimed_by": "",
            "claimed_at": ""
        }

        data = load_db()
        data.insert(0, new_post)
        save_db(data)

        flash("Post created successfully!", "success")
        return redirect(url_for('donor'))

    return render_template('donor.html')

# ================= NGO PAGE ============================
@app.route('/ngo')
def ngo():

    # ACCESS PROTECTION
    if session.get('role') != 'ngo':
        flash("Please login as NGO first!", "warning")
        return redirect(url_for('login'))

    posts = load_db()
    return render_template('ngo.html', posts=posts)

# ================= CLAIM FOOD ==========================
@app.route('/claim', methods=['POST'])
def claim():

    if session.get('role') != 'ngo':
        flash("Only NGO can claim!", "danger")
        return redirect(url_for('login'))

    post_id = request.form.get('post_id')
    claimer = request.form.get('claimer', 'NGO')

    data = load_db()

    for post in data:
        if str(post["id"]) == str(post_id):
            post["status"] = "Claimed"
            post["claimed_by"] = claimer
            post["claimed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break

    save_db(data)
    flash("Food claimed successfully!", "success")
    return redirect(url_for('ngo'))

# ================= RUN SERVER ==========================
if __name__ == '__main__':
    app.run(debug=True, port=5000)

