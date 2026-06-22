import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main_server import app, db, User, Admin, Disease
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def setup():
    with app.app_context():
        # Create all tables (drop first to reset schema)
        db.drop_all()
        db.create_all()
        
        # Check if admin exists
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(
                username='admin',
                email='admin@greenshield.com',
                password=bcrypt.generate_password_hash('admin123').decode('utf-8')
            )
            db.session.add(admin)
        
        # Add sample diseases based on the 10 classes in models/classes.txt
        sample_diseases = [
            {
                'name': 'Tomato___Bacterial_spot',
                'category': 'Bacterial',
                'symptoms': 'Small, water-soaked, greasy-looking spots on leaves. Raised, scab-like spots on fruit.',
                'prevention': 'Use pathogen-free seeds. Avoid overhead watering. Rotate crops.',
                'treatment': 'Apply copper-based bactericides at first sign of infection.',
                'fertilizers': 'Low nitrogen fertilizers during active infection.',
                'estimated_cost': 40.0,
                'recovery_time': '4-6 weeks'
            },
            {
                'name': 'Tomato___Early_blight',
                'category': 'Fungal',
                'symptoms': 'Brown/black spots with concentric rings (target pattern). Lower leaves usually affected first.',
                'prevention': 'Ensure proper spacing for airflow. Use mulch to prevent soil splashing.',
                'treatment': 'Fungicides containing chlorothalonil or copper. Remove infected lower leaves.',
                'fertilizers': 'Balanced NPK to maintain vigor.',
                'estimated_cost': 30.0,
                'recovery_time': '3-5 weeks'
            },
            {
                'name': 'Tomato___Late_blight',
                'category': 'Fungal',
                'symptoms': 'Rapidly spreading dark, water-soaked lesions. White fuzzy mold on leaf undersides.',
                'prevention': 'Plant resistant varieties. Avoid high humidity and overhead watering.',
                'treatment': 'Apply specialized late-blight fungicides immediately. Remove infected plants.',
                'fertilizers': 'Potassium-rich fertilizers to strengthen cell walls.',
                'estimated_cost': 50.0,
                'recovery_time': 'Variable (Highly Destructive)'
            },
            {
                'name': 'Tomato___Leaf_Mold',
                'category': 'Fungal',
                'symptoms': 'Pale green/yellow spots on upper leaf surface. Fuzzy gray/olive mold on undersides.',
                'prevention': 'Improve greenhouse ventilation. Reduce humidity levels.',
                'treatment': 'Apply fungicides like Chlorothalonil. Remove old leaves to improve airflow.',
                'fertilizers': 'Avoid excess nitrogen which promotes lush, susceptible growth.',
                'estimated_cost': 35.0,
                'recovery_time': '3-4 weeks'
            },
            {
                'name': 'Tomato___Septoria_leaf_spot',
                'category': 'Fungal',
                'symptoms': 'Small circular spots with gray centers and dark borders. Tiny black specks in the centers.',
                'prevention': 'Crop rotation. Remove previous year\'s tomato debris. Mulch.',
                'treatment': 'Apply fungicides. Prune lower branches to prevent soil-to-leaf contact.',
                'fertilizers': 'Nitrogen-balanced organic compost.',
                'estimated_cost': 25.0,
                'recovery_time': '2-3 weeks'
            },
            {
                'name': 'Tomato___Spider_mites Two-spotted_spider_mite',
                'category': 'Pest',
                'symptoms': 'Yellowing, bronze stippling on leaves. Fine silk webbing on leaf undersides.',
                'prevention': 'Increase humidity. Keep plants well-watered (mites love dry plants).',
                'treatment': 'Wash off with strong water stream. Use insecticidal soap or neem oil.',
                'fertilizers': 'Avoid high nitrogen which attracts mites.',
                'estimated_cost': 20.0,
                'recovery_time': '1-2 weeks'
            },
            {
                'name': 'Tomato___Target_Spot',
                'category': 'Fungal',
                'symptoms': 'Small brown spots with concentric rings (similar to early blight but smaller). Fruit lesions.',
                'prevention': 'Maintain wide spacing. Avoid long periods of leaf wetness.',
                'treatment': 'Protect with fungicides. Remove infected plant debris.',
                'fertilizers': 'Calcium-rich fertilizers.',
                'estimated_cost': 30.0,
                'recovery_time': '3-4 weeks'
            },
            {
                'name': 'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
                'category': 'Viral',
                'symptoms': 'Upward curling of leaves, yellow margins, stunted growth, flower drop.',
                'prevention': 'Control whitefly populations. Use insect-proof netting.',
                'treatment': 'No cure. Remove and destroy infected plants immediately.',
                'fertilizers': 'Micronutrient supplements to help plant tolerate stress.',
                'estimated_cost': 60.0,
                'recovery_time': 'N/A (Remove Plant)'
            },
            {
                'name': 'Tomato___Tomato_mosaic_virus',
                'category': 'Viral',
                'symptoms': 'Mottled green and yellow patterns (mosaic). Distorted, string-like leaves.',
                'prevention': 'Use certified virus-free seeds. Avoid handling plants after touching tobacco.',
                'treatment': 'No cure. Remove and destroy infected plants.',
                'fertilizers': 'N/A',
                'estimated_cost': 15.0,
                'recovery_time': 'N/A (Remove Plant)'
            },
            {
                'name': 'Tomato___healthy',
                'category': 'Healthy',
                'symptoms': 'Vibrant green leaves, sturdy stems, and normal growth patterns.',
                'prevention': 'Continue regular watering, mulching, and observation.',
                'treatment': 'N/A',
                'fertilizers': 'Organic compost or slow-release balanced fertilizer.',
                'estimated_cost': 0.0,
                'recovery_time': 'N/A'
            }
        ]
        
        for d in sample_diseases:
            existing = Disease.query.filter_by(name=d['name']).first()
            if not existing:
                disease = Disease(**d)
                db.session.add(disease)
            else:
                # Update existing record
                for key, value in d.items():
                    setattr(existing, key, value)
        
        db.session.commit()
        print("SUCCESS: Database updated with all 10 Tomato Disease classes!")

if __name__ == '__main__':
    setup()
