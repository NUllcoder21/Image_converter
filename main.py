from flask import Flask, render_template, request, flash, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import imageio.v2 as imageio  # Correct import for newer versions
from datetime import timedelta
from itsdangerous import URLSafeTimedSerializer
import os
import cv2
import numpy as np
import re  # Add this import at the top of your file

from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'webp', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = 'super_secret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Contect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    message = db.Column(db.String(100), nullable=False)
# Create database tables
with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def processImage(filename, operation,width=None,height=None):
    print(f"The operation is {operation} and filename is {filename}")
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    newfilename = f"static/{filename.split('.')[0]}"
    
    img = imageio.imread(filepath)
    if img is None:
        flash("Error loading image!")
        return None

    match operation:
        case "cgray":
            imgProcessed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            newfilename += ".png"
        case "cwebp":
            newfilename += ".webp"
        case "cjpg":
            newfilename += ".jpg"
        case "cpng":
            newfilename += ".png"
        case "cbmp":
            newfilename += ".bmp"
        case "ctiff":
            newfilename += ".tiff"
        case "cresized":
            if width and height:
                img = cv2.resize(img, (width, height))
            else:
                img = cv2.resize(img, (300, 300))  # Default size if no input given
            newfilename += "_resized.png"
        case "rotate":
            imgProcessed = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            newfilename += "_rotated.png"
        case "flip":
            imgProcessed = cv2.flip(img, 1)
            newfilename += "_flipped.png"
        case "cgif":
            newfilename += ".gif"
            imageio.mimsave(newfilename, [img], duration=0.5)
            return newfilename
        case "cpdf":
            newfilename += ".pdf"
            Image.fromarray(img).save(newfilename, "PDF")
            return newfilename
        case "cheic":
            newfilename += ".heic"
        case "capng":
            newfilename += ".apng"
        case "cico":
            newfilename += ".ico"
        case "craw":
            newfilename += ".raw"
        case "cdng":
            newfilename += ".dng"
        case "cexr":
            newfilename += ".exr"
        case "chdr":
            newfilename += ".hdr"
        case _:
            flash("Invalid operation!")
            return None
    
    imageio.imwrite(newfilename, imgProcessed if 'imgProcessed' in locals() else img)
    return newfilename
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/how")
def how():
    return render_template("how.html")

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        if not username or not email or not message:
            flash("All fields are required!", "danger")
            return redirect(url_for("contact"))

        # Save message in the Contect model
        new_message = Contect(username=username, email=email, message=message)
        db.session.add(new_message)
        db.session.commit()

        flash("Your message has been sent successfully!", "success")
        return redirect(url_for("contact"))

    return render_template('contact.html')


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"]

        # Email validation
        if not email:
            flash("Email field is required!", "danger")
            return redirect(url_for("signup"))

        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_regex, email):
            flash("Invalid email format!", "danger")
            return redirect(url_for("signup"))

        # Password strength validation
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
        if not re.match(password_regex, password):
            flash("Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.", "danger")
            return redirect(url_for("signup"))

        # Check for existing user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists. Please log in.", "warning")
            return redirect(url_for("login"))

        # Hash and save the password
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):

            session["user_id"] = user.id
            session["username"] = user.username
            flash(f"Login successful! Welcome, {session['username']}", "success")
            print("Session data:", session)  # Debugging line to check session values
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials. Please try again.", "danger")
    
    return render_template("login.html", forms={})

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    flash("Logged out successfully.")   
    return redirect(url_for("home"))

@app.route("/edit", methods=["GET", "POST"])
def edit():
    if "user_id" not in session:
        flash("You must sign up or log in first!", "danger")
        return redirect(url_for("login"))  

    if request.method == "POST":
        operation = request.form.get("operation")
        width = request.form.get("width")
        height = request.form.get("height")

        if width and height:
            width = int(width)
            height = int(height)

        if 'file' not in request.files:
            flash('No file part', "danger")
            return redirect(url_for("edit"))

        file = request.files['file']
        if file.filename == '':
            flash('No selected file', "danger")
            return redirect(url_for("edit"))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Pass width and height to processImage function
            processed_filepath = processImage(filename, operation, width, height)

            if processed_filepath:
                flash("Your image has been processed successfully.", "success")
                return render_template("index.html", processed_image=processed_filepath)

    return render_template("index.html")



@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, port=5000) 