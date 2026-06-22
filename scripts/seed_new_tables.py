import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main_server import app, db, Plant, Disease, PlantDisease, Recommendation

def seed():
    with app.app_context():
        print("Seeding new tables with sample data...")
        
        # 1. Add a sample Plant
        tomato_plant = Plant.query.filter_by(name='Tomato').first()
        if not tomato_plant:
            tomato_plant = Plant(name='Tomato', description='A widely cultivated edible fruit.')
            db.session.add(tomato_plant)
            db.session.commit()
            print("Added Plant: Tomato")
            
        # 2. Link Plant to Diseases (PlantDisease)
        diseases = Disease.query.all()
        for disease in diseases:
            link = PlantDisease.query.filter_by(plant_id=tomato_plant.id, disease_id=disease.id).first()
            if not link:
                link = PlantDisease(plant_id=tomato_plant.id, disease_id=disease.id)
                db.session.add(link)
        db.session.commit()
        print(f"Linked {len(diseases)} diseases to Tomato plant.")
        
        # 3. Add Recommendations for Diseases
        for disease in diseases:
            rec = Recommendation.query.filter_by(disease_id=disease.id).first()
            if not rec:
                rec = Recommendation(disease_id=disease.id, action_plan=f"General recommendation for {disease.name}: Follow prevention guidelines and apply recommended treatments as soon as symptoms appear.")
                db.session.add(rec)
        db.session.commit()
        print("Added sample recommendations for all diseases.")
        
        print("Done!")

if __name__ == '__main__':
    seed()
