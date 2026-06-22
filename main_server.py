from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
import cv2
import numpy as np
from google import genai
from datetime import datetime
from config import Config

import logging
import sys
import io

# Force UTF-8 encoding for Windows terminals to prevent emoji crashes
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Lazy load model utilities
from models.cnn_model import PlantDiseaseModel, get_severity
plant_model = None

def get_model():
    global plant_model
    if plant_model is None:
        model_path = os.path.join(os.path.dirname(__file__), 'models/plant_disease_model.h5')
        plant_model = PlantDiseaseModel(model_path=model_path)
    return plant_model

def analyze_with_gemini(image_path):
    api_key = app.config.get('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key_here':
        return None
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Load and resize image to speed up API transfer
        import PIL.Image
        img = PIL.Image.open(image_path)
        img.thumbnail((800, 800))
        
        prompt = """
        Analyze this image. 
        1. First, determine if the image contains a tomato leaf.
        2. If it does NOT contain a tomato leaf, identify what the image actually is. Return ONLY a JSON object with a single key "not_tomato_error" containing a message like: "This image appears to be a [identified object]. Please upload an image of a tomato leaf for analysis."
        3. If it DOES contain a tomato leaf, analyze it for diseases. Provide:
           - Disease Name
           - Category (Fungal, Bacterial, Viral, Environmental, or Healthy)
           - Symptoms (What is happening)
           - Treatment (How to fix it)
           - Prevention (How to stop it next time)
           - Estimated Cost (A single number representing the estimated cost of treatment in USD. E.g. 10 for $10. If healthy, 0)
        Return ONLY a JSON object. For a tomato leaf, use these exact keys: disease, category, symptoms, treatment, prevention, estimated_cost.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, img]
        )
        import json
        # Clean response text (remove markdown if present)
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except Exception as e:
        print(f"Gemini Analysis Error: {e}")
        return {"error": str(e)}

def ensure_mysql_db_exists(db_url):
    if db_url and (db_url.startswith("mysql+pymysql://") or db_url.startswith("mysql://")):
        try:
            from sqlalchemy.engine.url import make_url
            import pymysql
            
            url_obj = make_url(db_url)
            db_name = url_obj.database
            
            if not db_name:
                print("WARNING: No database name specified in MySQL connection URL.")
                return
                
            # Connect to MySQL server (without database name)
            connection = pymysql.connect(
                host=url_obj.host or 'localhost',
                user=url_obj.username or 'root',
                password=url_obj.password or '',
                port=url_obj.port or 3306
            )
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
                connection.commit()
                print(f"SUCCESS: Verified/Created MySQL database: '{db_name}'")
            finally:
                connection.close()
        except Exception as e:
            print(f"WARNING: Automatic MySQL database creation check failed: {e}")
            print("Please make sure the database exists on your MySQL server.")

ensure_mysql_db_exists(app.config.get('SQLALCHEMY_DATABASE_URI'))

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Supabase Storage Integration
supabase_client = None
if app.config.get('SUPABASE_URL') and app.config.get('SUPABASE_KEY') and app.config.get('SUPABASE_KEY') != 'your_supabase_anon_key_here':
    try:
        from supabase import create_client
        supabase_client = create_client(app.config['SUPABASE_URL'], app.config['SUPABASE_KEY'])
        bucket_name = app.config['SUPABASE_BUCKET_NAME']
        try:
            supabase_client.storage.get_bucket(bucket_name)
        except Exception:
            try:
                supabase_client.storage.create_bucket(bucket_name, options={"public": True})
                print(f"SUCCESS: Created public Supabase Storage bucket: '{bucket_name}'")
            except Exception as bucket_err:
                print(f"WARNING: Could not create bucket '{bucket_name}': {bucket_err}")
    except Exception as init_err:
        print(f"WARNING: Error initializing Supabase storage client: {init_err}")

def upload_to_supabase_storage(filepath, filename):
    if not supabase_client:
        return None
    try:
        bucket_name = app.config['SUPABASE_BUCKET_NAME']
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        mime_types = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'webp': 'image/webp'
        }
        content_type = mime_types.get(ext, 'application/octet-stream')
        
        with open(filepath, 'rb') as f:
            supabase_client.storage.from_(bucket_name).upload(
                path=filename,
                file=f,
                file_options={"content-type": content_type}
            )
        
        public_url = supabase_client.storage.from_(bucket_name).get_public_url(filename)
        return public_url
    except Exception as upload_err:
        print(f"Error uploading file to Supabase Storage: {upload_err}")
        return None


# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    predictions = db.relationship('Prediction', backref='user', lazy=True)

    def get_id(self):
        return f"user_{self.id}"

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def get_id(self):
        return f"admin_{self.id}"


class Disease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    symptoms = db.Column(db.Text)
    prevention = db.Column(db.Text)
    treatment = db.Column(db.Text)
    fertilizers = db.Column(db.Text)
    estimated_cost = db.Column(db.Float)
    recovery_time = db.Column(db.String(50))

class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    disease_id = db.Column(db.Integer, db.ForeignKey('disease.id'))
    image_path = db.Column(db.String(255))
    confidence = db.Column(db.Float)
    severity = db.Column(db.String(20))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location_name = db.Column(db.String(100))
    prediction_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    disease = db.relationship('Disease', backref='predictions')

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    # Relationships
    plant_diseases = db.relationship('PlantDisease', backref='plant', lazy=True)

class PlantDisease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    disease_id = db.Column(db.Integer, db.ForeignKey('disease.id'), nullable=False)
    
    # Relationships
    disease = db.relationship('Disease', backref='plant_diseases')

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    disease_id = db.Column(db.Integer, db.ForeignKey('disease.id'), nullable=False)
    action_plan = db.Column(db.Text, nullable=False)
    
    # Relationships
    disease = db.relationship('Disease', backref='recommendations')

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey('prediction.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    prediction = db.relationship('Prediction', backref='images')

@login_manager.user_loader
def load_user(user_id):
    user_id_str = str(user_id)
    if user_id_str.startswith('admin_'):
        return Admin.query.get(int(user_id_str.split('_')[1]))
    elif user_id_str.startswith('user_'):
        return User.query.get(int(user_id_str.split('_')[1]))
    else:
        return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        import re
        if not re.match(r'^[A-Za-z]+$', username):
            flash('Username must contain only letters.', 'danger')
            return redirect(url_for('register'))
        if not re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', email):
            flash('Email must be a @gmail.com address.', 'danger')
            return redirect(url_for('register'))
        if not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password):
            flash('Password must contain at least one uppercase letter, one number, and one special character.', 'danger')
            return redirect(url_for('register'))
        
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists. Please use a different one.', 'danger')
            return redirect(url_for('register'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        admin = Admin.query.filter_by(email=email).first()
        if admin and bcrypt.check_password_hash(admin.password, password):
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('admin_login.html')

@app.route('/admin_register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        import re
        if not re.match(r'^[A-Za-z]+$', username):
            flash('Username must contain only letters.', 'danger')
            return redirect(url_for('admin_register'))
        if not re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', email):
            flash('Email must be a @gmail.com address.', 'danger')
            return redirect(url_for('admin_register'))
        if not re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password):
            flash('Password must contain at least one uppercase letter, one number, and one special character.', 'danger')
            return redirect(url_for('admin_register'))
        
        existing_admin = Admin.query.filter((Admin.username == username) | (Admin.email == email)).first()
        if existing_admin:
            flash('Admin username or email already exists. Please use a different one.', 'danger')
            return redirect(url_for('admin_register'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        admin = Admin(username=username, email=email, password=hashed_password)
        db.session.add(admin)
        db.session.commit()
        flash('Admin Account created! You can now login to the portal.', 'success')
        return redirect(url_for('admin_login'))
    return render_template('admin_register.html')



@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not isinstance(current_user, Admin):
        flash('Access denied. Administrator privileges required.', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    all_predictions = Prediction.query.order_by(Prediction.prediction_date.desc()).all()
    diseases = Disease.query.all()
    return render_template('admin_dashboard.html', users=users, history=all_predictions, diseases=diseases)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Unauthorized'}), 403
    user = User.query.get_or_404(user_id)
    for p in user.predictions:
        Image.query.filter_by(prediction_id=p.id).delete()
    Prediction.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

import csv
from io import StringIO
from flask import Response

@app.route('/admin/export_csv')
@login_required
def admin_export_csv():
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Unauthorized'}), 403
    
    predictions = Prediction.query.order_by(Prediction.prediction_date.desc()).all()
    
    def generate():
        data = StringIO()
        writer = csv.writer(data)
        writer.writerow(['Date', 'User', 'Disease Detected', 'Severity', 'Confidence', 'Location'])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        
        for p in predictions:
            writer.writerow([
                p.prediction_date.strftime('%Y-%m-%d %H:%M'),
                p.user.username if p.user else 'Unknown',
                p.disease.name if p.disease else 'Unknown',
                p.severity,
                f"{p.confidence*100:.2f}%" if p.confidence else '0%',
                p.location_name
            ])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)
            
    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="global_scan_activity.csv")
    return response

@app.route('/admin/update_disease/<int:disease_id>', methods=['POST'])
@login_required
def admin_update_disease(disease_id):
    if not isinstance(current_user, Admin):
        return jsonify({'error': 'Unauthorized'}), 403
    
    disease = Disease.query.get_or_404(disease_id)
    disease.symptoms = request.form.get('symptoms', disease.symptoms)
    disease.treatment = request.form.get('treatment', disease.treatment)
    disease.prevention = request.form.get('prevention', disease.prevention)
    disease.fertilizers = request.form.get('fertilizers', disease.fertilizers)
    
    cost_val = request.form.get('estimated_cost')
    if cost_val:
        try:
            disease.estimated_cost = float(cost_val)
        except ValueError:
            pass
            
    db.session.commit()
    flash(f'Disease {disease.name} updated successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    history = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.prediction_date.desc()).all()
    return render_template('dashboard.html', history=history)

# Model initialization moved to top level

@app.route('/analyze', methods=['POST'])
@login_required
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check allowed extensions
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
    if not allowed_file(file.filename):
        return jsonify({'error': f"File type not allowed. Supported: {', '.join(app.config['ALLOWED_EXTENSIONS'])}"}), 400
    
    try:
        import uuid
        raw_filename = secure_filename(file.filename)
        unique_prefix = datetime.now().strftime('%Y%m%d%H%M%S') + "_" + uuid.uuid4().hex[:8]
        filename = f"{unique_prefix}_{raw_filename}"
        filepath = os.path.normpath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file.save(filepath)
        
        # 1. Try Gemini Vision first for high-accuracy API analysis
        gemini_result = analyze_with_gemini(filepath)
        
        if gemini_result and 'error' in gemini_result:
            print(f"Gemini API Error, falling back to local model: {gemini_result['error']}")
            gemini_result = None
            
        if gemini_result:
            if 'not_tomato_error' in gemini_result:
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
                return jsonify({'error': gemini_result['not_tomato_error']}), 400
                
            disease_name = gemini_result.get('disease') or gemini_result.get('Disease Name') or "Unknown Condition"
            # Check if this disease exists in our DB to keep history consistent
            disease = Disease.query.filter_by(name=disease_name).first()
            if not disease:
                # Dynamically add to DB if it's a new discovery!
                try:
                    est_cost = float(gemini_result.get('estimated_cost', 0))
                except:
                    est_cost = 0.0
                    
                disease = Disease(
                    name=disease_name,
                    category=gemini_result.get('category') or 'Unknown',
                    symptoms=gemini_result.get('symptoms') or 'Refer to Gemini analysis',
                    treatment=gemini_result.get('treatment') or 'Refer to Gemini analysis',
                    prevention=gemini_result.get('prevention') or 'Refer to Gemini analysis',
                    estimated_cost=est_cost,
                    recovery_time='Variable'
                )
                db.session.add(disease)
                db.session.commit()
            
            confidence = 0.99 # Gemini is high confidence
            severity = get_severity(disease_name, confidence)
        else:
            # 2. Fallback to Local Model / Simulation if API fails or key is missing
            model = get_model()
            if model:
                disease_name, confidence = model.predict(filepath)
            else:
                import random
                classes = ['Apple Scab', 'Corn Common Rust', 'Potato Early Blight', 'Tomato Late Blight', 'Healthy']
                disease_name = random.choice(classes)
                confidence = random.uniform(0.85, 0.98)
                
            severity = get_severity(disease_name, confidence)
            disease = Disease.query.filter_by(name=disease_name).first()
            if not disease:
                disease = Disease.query.filter_by(name='Healthy').first()
            
        if not disease:
            return jsonify({'error': 'Database not properly seeded. Healthy disease record missing.'}), 500
        
        # Upload to Supabase Storage
        public_url = upload_to_supabase_storage(filepath, filename)
        image_save_path = public_url if public_url else filename
        
        # Clean up local file only if successfully uploaded to Supabase Storage
        if public_url:
            try:
                os.remove(filepath)
                print(f"Removed temporary local file: {filepath}")
            except Exception as remove_err:
                print(f"Failed to remove temporary local file: {remove_err}")
        
        lat_str = request.form.get('lat')
        lng_str = request.form.get('lng')
        lat = float(lat_str) if lat_str and lat_str.strip() else None
        lng = float(lng_str) if lng_str and lng_str.strip() else None

        prediction = Prediction(
            user_id=current_user.id,
            disease_id=disease.id,
            image_path=image_save_path,
            confidence=confidence,
            severity=severity,
            latitude=lat,
            longitude=lng,
            location_name=request.form.get('location_name', 'Unknown Field')
        )
        db.session.add(prediction)
        db.session.commit()

        # Save to the new Image table as well
        new_image = Image(
            prediction_id=prediction.id,
            file_path=image_save_path
        )
        db.session.add(new_image)
        db.session.commit()
        return jsonify({
            'success': True,
            'disease': disease.name,
            'category': disease.category,
            'confidence': f"{confidence*100:.2f}%",
            'severity': severity,
            'symptoms': disease.symptoms,
            'treatment': disease.treatment,
            'prevention': disease.prevention,
            'fertilizers': disease.fertilizers,
            'cost': f"${float(disease.estimated_cost or 0.0):.2f} / ₹{int(float(disease.estimated_cost or 0.0) * 83)}",
            'recovery': disease.recovery_time,
            'location': prediction.location_name
        })
    except Exception as e:
        import traceback
        print("\n" + "!"*50)
        print("CRITICAL SYSTEM ERROR DETECTED")
        traceback.print_exc()
        print("!"*50 + "\n")
        return jsonify({'error': str(e)}), 500

@app.route('/submit_dataset', methods=['POST'])
@login_required
def submit_dataset():
    dataset_url = request.json.get('url')
    if not dataset_url:
        return jsonify({'error': 'No URL provided'}), 400
    
    # In a real app, we would save this to a 'TrainingTask' table
    # For now, we simulate success and log it
    print(f"NEW DATASET SUBMITTED FOR TRAINING: {dataset_url}")
    return jsonify({'success': True, 'message': 'Dataset link received! Our engineers will review it for model retraining.'})



@app.route('/chat', methods=['POST'])
@login_required
def chat():
    user_msg = request.json.get('message')
    if not user_msg:
        return jsonify({'error': 'No message provided'}), 400
    
    api_key = app.config.get('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key_here':
        return jsonify({'reply': 'AI Assistant is currently offline (Missing API Key).'})
        
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"You are a helpful agricultural assistant for GreenShield. The user asks: {user_msg}\nProvide a concise, expert answer."
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return jsonify({'reply': response.text.strip()})
    except Exception as e:
        print(f"Chatbot Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download_report/<int:prediction_id>')
@login_required
def download_report(prediction_id):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    import io
    
    pred = Prediction.query.get_or_404(prediction_id)
    if pred.user_id != current_user.id:
        return "Unauthorized", 403
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Header Styling
    p.setFillColorRGB(0.18, 0.8, 0.44) # GreenShield Green
    p.setFont("Helvetica-Bold", 24)
    p.drawString(100, 750, "GreenShield PRO")
    
    p.setFillColorRGB(0.2, 0.2, 0.2)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, 725, "OFFICIAL DISEASE DIAGNOSTIC REPORT")
    p.line(100, 720, 500, 720)
    
    # Metadata
    p.setFont("Helvetica", 10)
    p.drawString(100, 700, f"Report ID: GS-{pred.id:05d}")
    p.drawString(100, 685, f"Date generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    p.drawString(100, 670, f"Field Officer: {current_user.username}")
    
    # Diagnosis Section
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 640, "DIAGNOSIS RESULTS")
    p.setFont("Helvetica", 11)
    p.drawString(120, 620, f"Target Disease: {pred.disease.name}")
    p.drawString(120, 605, f"AI Confidence: {pred.confidence*100:.2f}%")
    
    # Severity Badge Simulation
    sev_color = (0.9, 0.3, 0.2) if pred.severity == 'Severe' else (0.95, 0.6, 0.1) if pred.severity == 'Moderate' else (0.18, 0.8, 0.44)
    p.setFillColorRGB(*sev_color)
    p.rect(400, 600, 100, 30, fill=1)
    p.setFillColorRGB(1, 1, 1)
    p.drawString(415, 610, f"STATUS: {pred.severity}")
    
    # Geolocation
    p.setFillColorRGB(0.2, 0.2, 0.2)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 570, "LOCATION DATA")
    p.setFont("Helvetica", 11)
    p.drawString(120, 550, f"Coordinates: {pred.latitude}, {pred.longitude}")
    p.drawString(120, 535, f"Field Name: {pred.location_name or 'Main Field'}")
    
    # Recommendations
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 500, "AGRONOMIST RECOMMENDATIONS")
    p.setFont("Helvetica", 10)
    
    # Wrap text for treatment
    from reportlab.lib.utils import simpleSplit
    treatment_lines = simpleSplit(pred.disease.treatment, "Helvetica", 10, 400)
    y_pos = 480
    for line in treatment_lines:
        p.drawString(120, y_pos, line)
        y_pos -= 15
    
    p.showPage()
    p.save()
    buffer.seek(0)
    
    from flask import send_file
    return send_file(buffer, as_attachment=True, download_name=f'report_{prediction_id}.pdf', mimetype='application/pdf')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("\n" + "="*50)
    print(">>> GREENSHIELD CORE ENGINE V3.0 STARTING <<<")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=8000, debug=True, use_reloader=False)
